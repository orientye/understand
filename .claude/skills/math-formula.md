---
name: math-formula
description: |
  Check AsciiDoc math expressions for dual-environment format correctness (ifndef::env-github / ifdef::env-github).
  Also suggest Unicode alternatives where possible to avoid formal math notation.
trigger: when the user asks to check or fix math formula formatting, or writes math expressions in .asc files
---

# Math Expression Format Checker

## What to Check

### 1. Dual-Format Compliance

Every formal math expression in `.asc` files must appear in both formats, wrapped in guards:

```asciidoc
ifndef::env-github[]
// Non-GitHub syntax
endif::[]
ifdef::env-github[]
// GitHub syntax
endif::[]
```

**Rules:**
- The two blocks MUST be adjacent — no text or blank lines between `endif::[]` and `ifdef::env-github[]`.
- Every opening guard must have a matching `endif::[]`.
- `ifndef::env-github[]` ... `endif::[]` must pair with `ifdef::env-github[]` ... `endif::[]` (one-to-one or many-to-many — but the same scope).
- Do NOT use `[source, math]` under any format.

### 2. Format Mapping

| Scope | Non-GitHub (`ifndef::env-github`) | GitHub (`ifdef::env-github`) |
|-------|-----------------------------------|------------------------------|
| Inline | `\(...\)`, `stem:[...]`, or `latexmath:[...]` | `$...$` |
| Block  | `\[...\]`, `[stem]++++...++++`, or `[latexmath]++++...++++` | `$$...$$` or `` ```math ... ``` `` |

- Prefer `[stem]++++` over `[latexmath]++++`, and `$$` over `` ```math ``` ``.
- `\(...\)` and `\[...\]` are less commonly used — double-check that they render correctly in your AsciiDoc toolchain.

### 3. Guard Coverage

Any paragraph or block containing a math expression — including `\(...\)`, `\[...\]`, `stem:[...]`, `latexmath:[...]`, `[stem]++++...++++`, `[latexmath]++++...++++` — must be entirely wrapped in guards.

### 4. Unicode-First Rule

Before writing a formal math expression, check whether the notation can be expressed with Unicode characters instead:

| Notation | Unicode |
|----------|---------|
| Transpose | `ᵀ` (e.g. `Aᵀ`) |
| Square root | `√` |
| Cube root | `∛` |
| Fourth root | `∜` |
| Subscripts | `₀₁₂₃₄₅₆₇₈₉ₙ` |
| Superscripts | `⁰¹²³⁴⁵⁶⁷⁸⁹` |
| Sum | `∑` |
| Product | `∏` |
| Integral | `∫` |
| Partial derivative | `∂` |
| Increment / Laplacian | `∆` |
| Infinity | `∞` |
| Not equal | `≠` |
| Less/greater or equal | `≤` `≥` |
| Multiply / divide | `×` `÷` |
| Plus-minus | `±` |
| Arrow | `→` |
| Element of | `∈` |
| Subset | `⊂` |
| Union / intersection | `∪` `∩` |
| For all / exists | `∀` `∃` |

Only fall back to `ifndef`/`ifdef` dual-format math when Unicode is insufficient (e.g. fractions, matrices, integrals with limits, complex layouts).

## When to Run This Check

- When new `.asc` files are added or modified.
- When the user explicitly asks to verify math formatting.
- During code review of changes touching math-heavy `.asc` files.
