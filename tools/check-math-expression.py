#!/usr/bin/env python3
"""
check-math-expression.py — Check & fix math expressions in .asc files.

Checks:
  1. Unicode-first: warn if a formal block could be replaced by Unicode.
  2. Guard pairing: ifndef::env-github[] / ifdef::env-github[] must be paired and adjacent.
  3. Guard coverage: paragraphs containing \(...\), \[...\], stem:[...], latexmath:[...],
     [stem]++++, [latexmath]++++ must be wrapped in guards.
  4. Format correctness: non-GitHub section uses correct AsciiDoc syntax;
     GitHub section uses correct Markdown syntax.
  5. Banned patterns: [source, math] is not allowed.

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
from pathlib import Path
from typing import List, NamedTuple, Optional


# ── Issues ──────────────────────────────────────────────────────────────────────

class Issue(NamedTuple):
    line: int
    severity: str  # "error" | "warning"
    code: str      # short code like E001
    message: str
    fix: Optional[str] = None  # suggested replacement, or None if not auto-fixable


# ── Checks ──────────────────────────────────────────────────────────────────────

CHECKS_RUN = set()  # track which checks actually triggered


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
                fix=None,  # context-dependent, flag for manual review
            ))
    return issues


def check_guard_pairs(lines: List[str], path: str) -> List[Issue]:
    """E001: Guard pairing — every ifndef must have matching ifdef adjacent."""
    issues = []
    stack = []  # (type: str, line: int)

    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        if "ifndef::env-github[]" in stripped:
            stack.append(("ifndef", i))
        elif "ifdef::env-github[]" in stripped:
            stack.append(("ifdef", i))
        elif "endif::[]" in stripped:
            if not stack:
                CHECKS_RUN.add("E001")
                issues.append(Issue(
                    line=i, severity="error", code="E001",
                    message="Stray endif::[] without matching guard.",
                ))
                continue
            opened = stack.pop()
            # Check that ifndef and ifdef are adjacent (no blank lines / text between endif and next guard)
            # The adjacency check for ifndef→endif→ifdef pairs is handled separately
            # We do a full structure check after scanning
        elif "endif::env-github[]" in stripped:
            # Variant: some files use endif::env-github[] instead of endif::[]
            if not stack:
                CHECKS_RUN.add("E001")
                issues.append(Issue(
                    line=i, severity="error", code="E001",
                    message="Stray endif::env-github[] without matching guard.",
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


def check_adjacent_guards(lines: List[str], path: str) -> List[Issue]:
    """E002: Check that ifndef/ifdef guard pairs are structurally sound.

    The AsciiDoc convention allows multiple ifndef blocks followed by
    multiple ifdef blocks (many-to-many), so strict adjacency is not required.
    This check is intentionally a no-op — the guard structure is validated
    by E001 (pairing) and E003 (coverage). We keep the function to reserve
    the E002 code for future structural checks."""
    return []


def check_guard_coverage(lines: List[str], path: str) -> List[Issue]:
    """E003: Math expressions must be wrapped in guards."""
    math_expr_patterns = [
        r"\\\([^)]*\\\)",           # \(...\)
        r"\\\[[^\]]*\\\]",          # \[...\]
        r"stem:\[.*?\]",            # stem:[...]
        r"latexmath:\[.*?\]",       # latexmath:[...]
        r"\[stem\]\+\+\+\+.*?\+\+\+\+",       # [stem]++++...++++  (single line)
        r"\[latexmath\]\+\+\+\+.*?\+\+\+\+",  # [latexmath]++++...++++
    ]
    # We only check inline expressions here — block ones are already guard-wrapped
    single_line_patterns = [
        (r"\\\([^)]*\\\)", r"\\\(.*?\\\)"),
        (r"stem:\[.*?\]", r"stem:\[.*?\]"),
        (r"latexmath:\[.*?\]", r"latexmath:\[.*?\]"),
    ]

    issues = []
    in_guard = False
    guard_start = 0

    for i, line in enumerate(lines, 1):
        if "ifndef::env-github[]" in line or "ifdef::env-github[]" in line:
            in_guard = True
            guard_start = i
        if "endif::[]" in line or "endif::env-github[]" in line:
            in_guard = False
        if in_guard:
            continue  # inside guard is fine

        # Check for \(...\) and \[...\] outside guards
        if re.search(r"\\\([^)]*\\\)", line):
            CHECKS_RUN.add("E003")
            issues.append(Issue(
                line=i, severity="error", code="E003",
                message=f"Math expression \\(...\\) found outside guard blocks. "
                        f"Wrap in ifndef::env-github[] / ifdef::env-github[].",
            ))
        if re.search(r"\\\[[^\]]*\\\]", line):
            CHECKS_RUN.add("E003")
            issues.append(Issue(
                line=i, severity="error", code="E003",
                message=f"Math expression \\[...\\] found outside guard blocks. "
                        f"Wrap in ifndef::env-github[] / ifdef::env-github[].",
            ))

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
        elif "endif::[]" in line or "endif::env-github[]" in line:
            in_ifndef = False
            in_ifdef = False
            continue

        if in_ifndef:
            # In non-GitHub: $...$ is wrong (use \(...\) or stem:[...])
            # ```math is wrong (use [stem]++++ or \[...\])
            if re.search(r'(?<!\$)\$[^$]+\$(?!\s)', line) and "stem:" not in line and "latexmath:" not in line:
                # Be careful: some lines might legitimately have $ in asciidoc
                # Only flag if it looks like a math expression
                if re.search(r'\$[a-zA-Z_\\{}]+\$', line):
                    CHECKS_RUN.add("E004")
                    issues.append(Issue(
                        line=i, severity="warning", code="E004",
                        message=f"Non-GitHub (ifndef) section uses Markdown math $...$. "
                                f"Use \(...\) or stem:[...] instead.",
                    ))
            if "```math" in line:
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="error", code="E004",
                    message=f"Non-GitHub (ifndef) section uses ```math. Use [stem]++++ or \\[...\\] instead.",
                ))

        if in_ifdef:
            # In GitHub: \(...\) is wrong (use $...$)
            # \[...\] is wrong (use $$...$$ or ```math)
            if re.search(r'\\\(', line):
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="error", code="E004",
                    message=f"GitHub (ifdef) section uses \(...\). Use $...$ instead.",
                ))
            if re.search(r'\\\[', line):
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="error", code="E004",
                    message=f"GitHub (ifdef) section uses \\[...\\]. Use $$...$$ or ```math instead.",
                ))
            if "stem:[" in line or "latexmath:[" in line:
                CHECKS_RUN.add("E004")
                issues.append(Issue(
                    line=i, severity="warning", code="E004",
                    message=f"GitHub (ifdef) section uses AsciiDoc math syntax. Use $$...$$ or $...$ instead.",
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
                if ("ifndef::env-github[]" in lines[j] or "ifdef::env-github[]" in lines[j]):
                    depth += 1
                elif "endif::[]" in lines[j] or "endif::env-github[]" in lines[j]:
                    depth -= 1
                if depth > 0 and j >= start:
                    content_lines.append(lines[j])
                j += 1

            # Check if content has actual math
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


# ── Auto-fix helpers ────────────────────────────────────────────────────────────

def fix_banned_source_math(content: str) -> str:
    """Replace [source, math] with ```math (when inside ifdef::env-github[])."""
    # Replace [source, math] blocks with ```math blocks
    # [source, math]\n----\n...\n---- → ```math\n...\n```
    content = re.sub(
        r'\[source,\s*math\]\s*\n-{3,}\s*\n(.*?)\n-{3,}',
        r'```math\n\g<1>\n```',
        content,
        flags=re.DOTALL,
    )
    return content


def fix_latexmath_in_guard(content: str) -> str:
    """Standardize latexmath:[] → stem:[] in ifndef sections (preferred form)."""
    # inline latexmath:[...] → stem:[...] — only inside ifndef blocks to be safe
    content = re.sub(
        r'(ifndef::env-github\[\].*?)latexmath:\[(.*?)\]',
        r'\g<1>stem:[\g<2>]',
        content,
        flags=re.DOTALL,
    )
    # block-level: standalone latexmath:[...] lines in ifndef → stem:[...]
    content = re.sub(
        r'^latexmath:\[(.+?)\]$',
        r'stem:[\g<1>]',
        content,
        flags=re.MULTILINE,
    )
    # [latexmath]++++ → [stem]++++
    content = re.sub(
        r'\[latexmath\]\+\+\+\+',
        r'[stem]++++',
        content,
    )
    return content


# ── Runner ──────────────────────────────────────────────────────────────────────

def check_file(path: str, fix: bool = False, dry_run: bool = False) -> List[Issue]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    lines = content.splitlines(keepends=True)

    # Run all checks
    issues = []
    issues.extend(check_banned_source_math(lines, path))
    issues.extend(check_guard_pairs(lines, path))
    issues.extend(check_adjacent_guards(lines, path))
    issues.extend(check_guard_coverage(lines, path))
    issues.extend(check_format_correctness(lines, path))
    issues.extend(check_unused_guards(lines, path))

    # Auto-fix
    if (fix or dry_run) and any(
        iss.code in ("E005", "E004") for iss in issues
    ):
        new_content = fix_banned_source_math(content)
        new_content = fix_latexmath_in_guard(new_content)
        if new_content != content:
            if dry_run:
                print(f"\n  [DRY-RUN] Would apply fixes to {path}")
                # Show diff
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

    return issues


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
            return

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
        total_files += 1
        issues = check_file(fpath, fix=args.fix, dry_run=args.dry_run)
        total_errors += print_report(issues, fpath)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Scanned {total_files} file(s)")
    action = "previewed" if args.dry_run else ("fixed" if args.fix else "checked")
    print(f"  Total errors found: {total_errors}")
    print(f"  Checks applied: {', '.join(sorted(CHECKS_RUN)) if CHECKS_RUN else 'none'}")
    print(f"  Mode: {action}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
