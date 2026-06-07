---
name: check-math-expression
description: |
  Check and auto-fix dual-format math in .asc files (ifndef::env-github /
  ifdef::env-github guards). Use when editing .asc math, verifying formatting,
  the user asks to check math formatting, or before committing math-heavy changes.
---

# Math Expression Checker

## What It Does

Runs `tools/check-math-expression.py` on `.asc` files to detect and auto-fix math
formatting issues. Format rules are defined in [.claude/CLAUDE.md](.claude/CLAUDE.md).

## Agent Workflow

1. **Check first** (no flags) on changed `.asc` file(s).
2. If auto-fixable issues exist (`E005`, `latexmath` → `stem`), run `--dry-run` to preview.
3. Apply `--fix` only after preview looks correct. `--dry-run` and `--fix` are mutually exclusive.
4. **Re-check** after fixing; repeat until `Total errors found: 0`.
5. Manually fix anything still reported:
   - **E001 / E003** — guard structure and coverage (needs human judgment).
   - **E004 errors** — wrong syntax for the target environment.
   - **E006** — `$...$` touching CJK characters (GitHub MathJax cannot render).
   - **W001 / W002** — warnings only; consider removing unnecessary guards or using Unicode.
6. Script exits with code **1** when errors remain — do not treat a non-zero exit as success.

## Checks Performed

### E001 — Guard Pairing
`ifndef::env-github[]` and `ifdef::env-github[]` must each have a matching `endif::[]`
(or `endif::env-github[]`).

### E003 — Guard Coverage
Math expressions found outside guard blocks are flagged:
`\(...\)`, `\[...\]`, `stem:[...]`, `latexmath:[...]`, `[stem]++++...++++`,
`[latexmath]++++...++++`, `$...$`, `$$...$$`, ` ```math `.

### E004 — Format Correctness
- **ifndef** (non-GitHub): AsciiDoc — `\(...\)`, `stem:[...]`, `[stem]++++`
- **ifdef** (GitHub): Markdown — `$...$`, `$$...$$`, ` ```math `

Some E004 findings are **warnings** (wrong syntax in the other environment's style,
e.g. `$...$` inside ifndef, `stem:[...]` inside ifdef).

### E005 — Banned Patterns
`[source, math]` is banned everywhere.

### W001 — Unnecessary Guards
Guard blocks with no math content.

### W002 — Unicode Candidates
Simple inline math inside guards (e.g. `x^2`, `A^T`) that may be replaceable with
Unicode per CLAUDE.md, avoiding dual-format guards entirely.

## Usage

```bash
# Check a single file
python tools/check-math-expression.py path/to/file.asc

# Preview auto-fixes (cannot combine with --fix)
python tools/check-math-expression.py path/to/file.asc --dry-run

# Check + auto-fix, then re-check
python tools/check-math-expression.py path/to/file.asc --fix
python tools/check-math-expression.py path/to/file.asc

# Check / fix all .asc files
python tools/check-math-expression.py --all
python tools/check-math-expression.py --all --fix
```

## Auto-Fix Capabilities

| Issue | Auto-Fix? | What it does |
|-------|-----------|-------------|
| `[source, math]` | ✅ | Replaces with ` ```math ` block **inside ifdef only** |
| `[latexmath]++++` | ✅ | Replaces with `[stem]++++` in ifndef sections |
| `latexmath:[]` | ✅ | Replaces with `stem:[]` in ifndef sections |
| Guard pairing (E001) | ❌ | Report only |
| Guard coverage (E003) | ❌ | Report only |
| Format correctness (E004) | ❌ | Report only |
| `$...$` touching CJK (E006) | ❌ | Report only |
| Unicode candidates (W002) | ❌ | Report only |
