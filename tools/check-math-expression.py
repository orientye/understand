#!/usr/bin/env python3
"""
check-math-expression.py — Check & fix math expressions in .asc files.

Checks:
  1. Guard pairing: ifndef::env-github[] / ifdef::env-github[] must be paired.
  2. Guard coverage: math expressions must be wrapped in guards.
  3. Format correctness: AsciiDoc in ifndef, Markdown in ifdef.
  4. Banned patterns: [source, math] is not allowed.
  5. W001: unnecessary guard blocks; W002: simple math that could use Unicode.

Usage:
  python tools/check-math-expression.py <file.asc>              # check only
  python tools/check-math-expression.py <file.asc> --fix        # check + auto-fix
  python tools/check-math-expression.py <file.asc> --dry-run    # preview fixes
  python tools/check-math-expression.py --all                   # check all .asc files
  python tools/check-math-expression.py --all --fix             # fix all .asc files
"""

import argparse
import os
import re
import sys
from typing import List, NamedTuple, Optional, Tuple


# ── Issues ──────────────────────────────────────────────────────────────────────

class Issue(NamedTuple):
    line: int
    severity: str  # "error" | "warning"
    code: str      # short code like E001
    message: str
    fix: Optional[str] = None


# ── Checks ──────────────────────────────────────────────────────────────────────

CHECKS_RUN = set()

# Simple inline math that CLAUDE.md says should prefer Unicode (no dual-format guards).
_UNICODE_CANDIDATE = re.compile(
    r"^(?:"
    r"[a-zA-Z](?:\^|_)(?:[0-9n]|T)|"           # x^2, a_n, A^T
    r"[a-zA-Z]\^\{[0-9nT]\}|"                  # x^{2}, A^{T}
    r"[a-zA-Z]_\{[0-9n]\}|"                    # x_{1}
    r"\\sqrt\{[a-zA-Z0-9]+\}|"                # \sqrt{x}
    r"\\neq|\\leq|\\geq|\\times|\\pm"          # common symbols
    r")$"
)

# CJK 字符范围：汉字 + 中文标点
_CJK_RE = re.compile(
    r'[一-鿿㐀-䶿＀-￯　-〿 -⁯]'
)


def _is_cjk(ch: str) -> bool:
    """Check if a character is CJK (Chinese/Japanese/Korean) or CJK punctuation."""
    return bool(_CJK_RE.match(ch))


def _is_guard_open(line: str) -> bool:
    return "ifndef::env-github[]" in line or "ifdef::env-github[]" in line


def _is_guard_close(line: str) -> bool:
    return "endif::[]" in line or "endif::env-github[]" in line


def check_banned_source_math(lines: List[str], path: str) -> List[Issue]:
    """E005: [source, math] is banned."""
    issues = []
    for i, line in enumerate(lines, 1):
        if "[source, math]" in line:
            CHECKS_RUN.add("E005")
            issues.append(Issue(
                line=i,
                severity="error",
                code="E005",
                message="[source, math] is banned. Use [stem]++++ (non-GitHub) and ```math (GitHub) instead.",
            ))
    return issues


def check_guard_pairs(lines: List[str], path: str) -> List[Issue]:
    """E001: Guard pairing — every opening guard must have a matching endif."""
    issues = []
    stack = []

    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        if "ifndef::env-github[]" in stripped:
            stack.append(("ifndef", i))
        elif "ifdef::env-github[]" in stripped:
            stack.append(("ifdef", i))
        elif "endif::[]" in stripped or "endif::env-github[]" in stripped:
            if not stack:
                CHECKS_RUN.add("E001")
                issues.append(Issue(
                    line=i, severity="error", code="E001",
                    message="Stray endif without matching guard.",
                ))
                continue
            stack.pop()

    if stack:
        CHECKS_RUN.add("E001")
        for ty, ln in stack:
            issues.append(Issue(
                line=ln, severity="error", code="E001",
                message=f"Unclosed {ty}::env-github[] guard (no matching endif::[]).",
            ))

    return issues


def _report_e003(issues: List[Issue], line: int, expr: str) -> None:
    CHECKS_RUN.add("E003")
    issues.append(Issue(
        line=line, severity="error", code="E003",
        message=f"Math expression {expr} found outside guard blocks. "
                f"Wrap in ifndef::env-github[] / ifdef::env-github[].",
    ))


def check_guard_coverage(lines: List[str], path: str) -> List[Issue]:
    """E003: Math expressions must be wrapped in guards."""
    issues = []
    in_guard = False
    in_stem_block = False
    in_latexmath_block = False

    for i, line in enumerate(lines, 1):
        if _is_guard_open(line):
            in_guard = True
        if _is_guard_close(line):
            in_guard = False
            in_stem_block = False
            in_latexmath_block = False

        if in_guard:
            continue

        stripped = line.strip()

        if in_stem_block:
            if stripped == "++++":
                in_stem_block = False
            continue

        if in_latexmath_block:
            if stripped == "++++":
                in_latexmath_block = False
            continue

        if "[stem]++++" in line:
            in_stem_block = True
            _report_e003(issues, i, "[stem]++++...++++")
            continue

        if "[latexmath]++++" in line:
            in_latexmath_block = True
            _report_e003(issues, i, "[latexmath]++++...++++")
            continue

        if re.search(r"\\\([^)]*\\\)", line):
            _report_e003(issues, i, "\\(...\\)")
        if re.search(r"\\\[[^\]]*\\\]", line):
            _report_e003(issues, i, "\\[...\\]")
        if re.search(r"stem:\[[^\]]+\]", line):
            _report_e003(issues, i, "stem:[...]")
        if re.search(r"latexmath:\[[^\]]+\]", line):
            _report_e003(issues, i, "latexmath:[...]")
        if re.search(r"(?<!\$)\$[^$\n]+\$(?!\$)", line):
            _report_e003(issues, i, "$...$")
        if re.search(r"\$\$[^$]+\$\$", line):
            _report_e003(issues, i, "$$...$$")
        if "```math" in line:
            _report_e003(issues, i, "```math")

    return issues


def check_format_correctness(lines: List[str], path: str) -> List[Issue]:
    """E004: Check format correctness — asciidoc in ifndef, markdown in ifdef."""
    issues = []
    in_ifndef = False
    in_ifdef = False

    for i, line in enumerate(lines, 1):
        if "ifndef::env-github[]" in line:
            in_ifndef = True
            in_ifdef = False
        elif "ifdef::env-github[]" in line:
            in_ifdef = True
            in_ifndef = False
        elif _is_guard_close(line):
            in_ifndef = False
            in_ifdef = False
            continue

        if in_ifndef:
            if re.search(r'(?<!\$)\$[^$]+\$(?!\$)', line) and "stem:" not in line and "latexmath:" not in line:
                if re.search(r'\$[a-zA-Z_\\{}]+\$', line):
                    CHECKS_RUN.add("E004")
                    issues.append(Issue(
                        line=i, severity="warning", code="E004",
                        message="Non-GitHub (ifndef) section uses Markdown math $...$. "
                                "Use \\(...\\) or stem:[...] instead.",
                    ))
            if "```math" in line:
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="error", code="E004",
                    message="Non-GitHub (ifndef) section uses ```math. Use [stem]++++ or \\[...\\] instead.",
                ))

        if in_ifdef:
            if re.search(r'\\\(', line):
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="error", code="E004",
                    message="GitHub (ifdef) section uses \\(...\\). Use $...$ instead.",
                ))
            if re.search(r'\\\[', line):
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="error", code="E004",
                    message="GitHub (ifdef) section uses \\[...\\]. Use $$...$$ or ```math instead.",
                ))
            if "stem:[" in line or "latexmath:[" in line:
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="warning", code="E004",
                    message="GitHub (ifdef) section uses AsciiDoc math syntax. Use $$...$$ or $...$ instead.",
                ))

            # E006: $...$ 前紧贴中文字符/中文标点，GitHub MathJax 渲染失败
            # （$...$ 后紧贴中文标点通常能正常渲染，不报错）
            for m in re.finditer(r'(?<!\$)\$[^$\n]+\$(?!\$)', line):
                match = m.group()
                start = m.start()
                # 跳过独立成行的 $$...$$
                if match.startswith('$$') and match.endswith('$$'):
                    continue
                # 只检查 $ 前面
                if start > 0:
                    prev = line[start - 1]
                    if _is_cjk(prev):
                        CHECKS_RUN.add("E006")
                        issues.append(Issue(
                            line=i, severity="error", code="E006",
                            message=f"'{match}' 前紧贴中文字符 '{prev}'，GitHub MathJax 无法渲染。请在 '$' 前加空格。",
                        ))

    return issues


def _extract_math_inner(line: str) -> Optional[str]:
    """Return inner content of a simple inline math expression, or None."""
    for pattern in (
        r"stem:\[([^\]]+)\]",
        r"latexmath:\[([^\]]+)\]",
        r"\\\(([^)]*)\\\)",
        r"(?<!\$)\$([^$\n]+)\$(?!\$)",
    ):
        m = re.search(pattern, line)
        if m:
            return m.group(1).strip()
    return None


def check_unicode_candidates(lines: List[str], path: str) -> List[Issue]:
    """W002: Warn when simple math could use Unicode instead of dual-format guards."""
    issues = []
    in_guard = False
    guard_line = 0

    for i, line in enumerate(lines, 1):
        if _is_guard_open(line):
            in_guard = True
            guard_line = i
        if _is_guard_close(line):
            in_guard = False

        if not in_guard:
            continue

        inner = _extract_math_inner(line)
        if inner and _UNICODE_CANDIDATE.match(inner):
            CHECKS_RUN.add("W002")
            issues.append(Issue(
                line=i, severity="warning", code="W002",
                message=f"Simple math '{inner}' may be replaceable with Unicode characters "
                        f"(see .claude/CLAUDE.md). Guard block at line {guard_line} may be unnecessary.",
            ))

    return issues


def check_unused_guards(lines: List[str], path: str) -> List[Issue]:
    """W001: Warn if a guard block contains no math content."""
    issues = []
    i = 0
    while i < len(lines):
        line = lines[i]
        guard_type = None
        if "ifndef::env-github[]" in line:
            guard_type = "ifndef"
        elif "ifdef::env-github[]" in line:
            guard_type = "ifdef"

        if guard_type:
            start = i + 1
            j = i + 1
            depth = 1
            content_lines = []
            while j < len(lines) and depth > 0:
                if _is_guard_open(lines[j]):
                    depth += 1
                elif _is_guard_close(lines[j]):
                    depth -= 1
                if depth > 0 and j >= start:
                    content_lines.append(lines[j])
                j += 1

            has_math = any(
                re.search(r'stem:|latexmath:|\\\\\(|\\\\\[|\$|```math|\[stem\]|\[latexmath\]', cl)
                for cl in content_lines
            )
            if not has_math and content_lines and any(cl.strip() for cl in content_lines):
                CHECKS_RUN.add("W001")
                issues.append(Issue(
                    line=i + 1, severity="warning", code="W001",
                    message=f"Guard block (line {i+1}) contains no math expressions. "
                            f"It may be unnecessary or missing math content.",
                ))
            i = j
        else:
            i += 1
    return issues


def run_checks(lines: List[str], path: str) -> List[Issue]:
    issues = []
    issues.extend(check_banned_source_math(lines, path))
    issues.extend(check_guard_pairs(lines, path))
    issues.extend(check_guard_coverage(lines, path))
    issues.extend(check_format_correctness(lines, path))
    issues.extend(check_unicode_candidates(lines, path))
    issues.extend(check_unused_guards(lines, path))
    return issues


# ── Auto-fix helpers ────────────────────────────────────────────────────────────

def fix_banned_source_math(content: str) -> str:
    """Replace [source, math] with ```math only inside ifdef::env-github[] blocks."""
    lines = content.splitlines(keepends=True)
    result: List[str] = []
    in_ifdef = False
    i = 0

    while i < len(lines):
        line = lines[i]
        if "ifdef::env-github[]" in line:
            in_ifdef = True
            result.append(line)
            i += 1
            continue
        if "ifndef::env-github[]" in line:
            in_ifdef = False
            result.append(line)
            i += 1
            continue
        if _is_guard_close(line):
            in_ifdef = False
            result.append(line)
            i += 1
            continue

        if in_ifdef and "[source, math]" in line:
            block_lines = [line]
            j = i + 1
            replaced = False
            if j < len(lines) and re.match(r"-{3,}\s*$", lines[j].strip()):
                block_lines.append(lines[j])
                j += 1
                body = []
                while j < len(lines) and not re.match(r"-{3,}\s*$", lines[j].strip()):
                    body.append(lines[j])
                    j += 1
                if j < len(lines):
                    block_lines.append(lines[j])
                    result.append("```math\n")
                    result.extend(body)
                    result.append("```\n")
                    i = j + 1
                    replaced = True
            if not replaced:
                result.append(line)
                i += 1
            continue

        result.append(line)
        i += 1

    return "".join(result)


def fix_latexmath_in_guard(content: str) -> str:
    """Standardize latexmath → stem in ifndef sections (preferred form)."""
    parts = re.split(r"(ifndef::env-github\[\])", content)
    if len(parts) == 1:
        content = re.sub(r"\[latexmath\]\+\+\+\+", "[stem]++++", content)
        return content

    rebuilt = [parts[0]]
    idx = 1
    while idx < len(parts):
        rebuilt.append(parts[idx])
        idx += 1
        if idx >= len(parts):
            break
        section = parts[idx]
        idx += 1
        end = section.find("endif::")
        if end == -1:
            block, rest = section, ""
        else:
            block, rest = section[:end], section[end:]
        block = re.sub(r"latexmath:\[([^\]]*)\]", r"stem:[\1]", block)
        block = re.sub(r"\[latexmath\]\+\+\+\+", "[stem]++++", block)
        rebuilt.append(block + rest)

    return "".join(rebuilt)


def apply_auto_fixes(content: str) -> Tuple[str, bool]:
    new_content = fix_latexmath_in_guard(content)
    new_content = fix_banned_source_math(new_content)
    return new_content, new_content != content


# ── Runner ──────────────────────────────────────────────────────────────────────

def check_file(path: str, fix: bool = False, dry_run: bool = False) -> List[Issue]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if fix or dry_run:
        new_content, changed = apply_auto_fixes(content)
        if changed:
            if dry_run:
                print(f"\n  [DRY-RUN] Would apply fixes to {path}")
                from difflib import unified_diff
                diff = unified_diff(
                    content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                )
                for dline in diff:
                    print(f"    {dline}", end="")
            elif fix:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  [FIXED] {path}")
            content = new_content

    lines = content.splitlines(keepends=True)
    return run_checks(lines, path)


def print_report(issues: List[Issue], path: str) -> int:
    if not issues:
        return 0

    errors = [i for i in issues if i.severity == "error"]
    warnings_ = [i for i in issues if i.severity == "warning"]

    print(f"\n{'='*60}")
    print(f"  {path}")
    print(f"{'='*60}")

    for iss in issues:
        icon = "[X]" if iss.severity == "error" else "[!]"
        print(f"  {icon} L{iss.line:>4} [{iss.code}] {iss.message}")

    print(f"\n  Summary: {len(errors)} errors, {len(warnings_)} warnings")
    return len(errors)


def find_all_asc_files(root: str) -> List[str]:
    matches = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".asc"):
                matches.append(os.path.join(dirpath, fn))
    return sorted(matches)


def main():
    global CHECKS_RUN
    parser = argparse.ArgumentParser(description="Check & fix math expressions in .asc files")
    parser.add_argument("files", nargs="*", help=".asc file(s) to check")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--dry-run", action="store_true", help="Preview fixes without applying")
    parser.add_argument("--all", action="store_true", help="Check all .asc files in repo")
    args = parser.parse_args()

    files = args.files
    if args.all:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        files = find_all_asc_files(repo_root)
        if not files:
            print("No .asc files found.")
            sys.exit(0)

    if args.dry_run and args.fix:
        print("Cannot use --dry-run and --fix together. Use --dry-run for preview.")
        sys.exit(1)

    if not files:
        parser.print_help()
        sys.exit(1)

    total_errors = 0
    total_files = 0

    for fpath in files:
        if not os.path.exists(fpath):
            print(f"  ⚠ File not found: {fpath}")
            continue
        CHECKS_RUN = set()
        total_files += 1
        issues = check_file(fpath, fix=args.fix, dry_run=args.dry_run)
        total_errors += print_report(issues, fpath)

    print(f"\n{'='*60}")
    print(f"  Scanned {total_files} file(s)")
    action = "previewed" if args.dry_run else ("fixed" if args.fix else "checked")
    print(f"  Total errors found: {total_errors}")
    print(f"  Mode: {action}")
    print(f"{'='*60}\n")

    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
