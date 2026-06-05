# CLAUDE.md

- Plain text docs only — no build system, no tests, no package manager.
- Prefer Unicode math characters over formal math expressions where possible, to avoid dual-format complexity:
  - Transpose: `ᵀ` (e.g. `Aᵀ`)
  - Square root: `√`, cube root: `∛`, fourth root: `∜`
  - Subscripts: `₀₁₂₃₄₅₆₇₈₉ₙ` (e.g. `x₁`, `aₙ`)
  - Superscripts: `⁰¹²³⁴⁵⁶⁷⁸⁹` (e.g. `x²`, `aⁿ`)
  - Other common symbols: `∑`, `∏`, `∫`, `∂`, `∆`, `∞`, `≠`, `≤`, `≥`, `×`, `÷`, `±`, `→`, `∈`, `⊂`, `∪`, `∩`, `∀`, `∃`
  - Only fall back to `ifndef`/`ifdef` dual-format math expressions when the notation is too complex for Unicode.
- Math formulas must support dual formats:
  - **Non-GitHub** (`ifndef::env-github[]` ... `endif::[]`): use AsciiDoc native syntax.
  - **GitHub** (`ifdef::env-github[]` ... `endif::[]`): use GitHub-flavored Markdown syntax.

  | Scope | Non-GitHub (`ifndef::env-github`) | GitHub (`ifdef::env-github`) |
  |-------|-----------------------------------|------------------------------|
  | Inline | `\(...\)`, `stem:[...]`, or `latexmath:[...]` | `$...$` |
  | Block  | `\[...\]`, `[stem]++++...++++`, or `[latexmath]++++...++++` | `$$...$$` or `` ```math ... ``` `` |

  > **Note:** The `[latexmath]++++...++++` block form and `` ```math ... ``` `` block form are not recommended — prefer `[stem]++++...++++` and `$$...$$` respectively.
  >
  > **Important:** Any paragraph or block containing a math expression (`\(...\)`, `\[...\]`, `stem:[...]`, `latexmath:[...]`, `[stem]++++...++++`, `[latexmath]++++...++++`) must be entirely wrapped in `ifndef`/`ifdef` guards, otherwise GitHub will fail to render it.
  >
  > Do NOT use `[source, math]` under any format.