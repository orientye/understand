---
name: check-math-expression
description: |
  Check and auto-fix math expressions in .asc files for dual-environment format
  correctness (ifndef::env-github / ifdef::env-github) and Unicode optimization.
trigger: when the user asks to check math formatting, or when .asc files with math are modified
---

# Math Expression Checker

## What It Does

This skill runs `tools/check-math-expression.py` on `.asc` files to automatically detect and fix math formatting issues.

## Checks Performed

### E001 — Guard Pairing
`ifndef::env-github[]` and `ifdef::env-github[]` must be paired correctly (every opening has a matching `endif::[]`).

### E002 — Adjacent Guards
The `ifndef` block and `ifdef` block must be adjacent — no content between the closing `endif::[]` and the next opening guard.

### E003 — Guard Coverage
Math expressions (`\(...\)`, `\[...\]`, `stem:[...]`, `latexmath:[...]`, `[stem]++++`) found outside guard blocks are flagged.

### E004 — Format Correctness
- Non-GitHub section (ifndef) should use AsciiDoc syntax: `\(...\)` / `stem:[...]` / `[stem]++++`
- GitHub section (ifdef) should use Markdown syntax: `$...$` / `$$...$$` / ```` ```math ````

### E005 — Banned Patterns
`[source, math]` is banned. Auto-fixed to ` ```math ` in ifdef sections.

### W001 — Unnecessary Guards
Guard blocks containing no math expressions are flagged as warnings.

## Usage

```bash
# Check a single file
python tools/check-math-expression.py path/to/file.asc

# Check + auto-fix
python tools/check-math-expression.py path/to/file.asc --fix

# Preview fixes without applying
python tools/check-math-expression.py path/to/file.asc --dry-run

# Check all .asc files in the repo
python tools/check-math-expression.py --all

# Fix all .asc files
python tools/check-math-expression.py --all --fix
```

## When to Run

- When `.asc` files with math expressions are created or modified.
- When the user explicitly asks to verify math formatting.
- Before committing math-heavy changes.

## Auto-Fix Capabilities

| Issue | Auto-Fix? | What it does |
|-------|-----------|-------------|
| `[source, math]` | ✅ | Replaces with ` ```math ` block |
| `[latexmath]++++` | ✅ | Replaces with `[stem]++++` |
| `latexmath:[]` | ✅ | Replaces with `stem:[]` |
| Guard pairing | ❌ | Report only (context-dependent) |
| Guard coverage | ❌ | Report only (needs human judgment) |
