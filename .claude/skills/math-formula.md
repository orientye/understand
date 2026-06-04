---
name: math-formula
description: |
  Write AsciiDoc math formulas with dual-environment support (GitHub + non-GitHub).
  Inline: non-GitHub uses latexmath:[], GitHub uses $ $.
  Block: non-GitHub uses \[ \], GitHub uses $$ $$.
trigger: when the user asks about writing math formulas, LaTeX, AsciiMath, or KaTeX in AsciiDoc, or asks for help formatting mathematical expressions in this repo
---

# Writing Math Formulas in AsciiDoc (Dual-Environment)

## The Problem

This repo uses **AsciiDoc (`.asc`)** format, which natively supports math via `latexmath:[]` macro and `\[ \]` block syntax. However, **GitHub's AsciiDoc renderer does not support those** — it renders formulas as raw text. To make formulas render correctly on both GitHub (`env-github`) and locally/non-GitHub, you must wrap each formula in `ifdef`/`ifndef` conditional blocks.

## Pattern: Guard Every Formula

Every formula must appear **twice** — once for each environment:

```asciidoc
ifndef::env-github[]
// non-GitHub syntax
endif::[]
ifdef::env-github[]
// GitHub syntax
endif::[]
```

> ⚠️ The two blocks MUST be adjacent — do not put text or blank lines between `endif::[]` and `ifdef::env-github[]`.

## Inline Formulas

| Environment | Syntax |
|---|---|
| Non-GitHub | `latexmath:[formula]` |
| GitHub | `$formula$` |

### Example

```asciidoc
ifndef::env-github[]
牛顿法搜索方向: latexmath:[\mathbf{x}_{k+1} = \mathbf{x}_k - [\nabla^2 f(\mathbf{x}_k)]^{-1} \nabla f(\mathbf{x}_k)]
endif::[]
ifdef::env-github[]
牛顿法搜索方向: $\mathbf{x}_{k+1} = \mathbf{x}_k - [\nabla^2 f(\mathbf{x}_k)]^{-1} \nabla f(\mathbf{x}_k)$
endif::[]
```

## Block Formulas

| Environment | Syntax |
|---|---|
| Non-GitHub | `\[ ... \]` |
| GitHub | `$$ ... $$` |

### Example

```asciidoc
ifndef::env-github[]
\[
P(B|A) = \frac{P(A \cap B)}{P(A)}
\]
endif::[]
ifdef::env-github[]
$$
P(B|A) = \frac{P(A \cap B)}{P(A)}
$$
endif::[]
```

> ⚠️ In non-GitHub, the `\[` and `\]` lines must be separated from text by blank lines, otherwise they may be treated as inline text.

## Common Patterns

### Derivatives

```asciidoc
ifndef::env-github[]
latexmath:[\frac{dy}{dx} = \lim_{\Delta x \to 0} \frac{\Delta y}{\Delta x}]

\[
\int_a^b f(x) \, dx = F(b) - F(a)
\]
endif::[]
ifdef::env-github[]
$\frac{dy}{dx} = \lim_{\Delta x \to 0} \frac{\Delta y}{\Delta x}$

$$
\int_a^b f(x) \, dx = F(b) - F(a)
$$
endif::[]
```

### Matrices

```asciidoc
ifndef::env-github[]
\[
A = \begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}
\]
endif::[]
ifdef::env-github[]
$$
A = \begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}
$$
endif::[]
```

### Summations

```asciidoc
ifndef::env-github[]
latexmath:[\sum_{i=1}^{n} i = \frac{n(n+1)}{2}]

\[
\sigma(x) = \frac{1}{1 + e^{-x}}
\]
endif::[]
ifdef::env-github[]
$\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$

$$
\sigma(x) = \frac{1}{1 + e^{-x}}
$$
endif::[]
```

## Shortcut: Inline Only (When Block is Overkill)

For very short formulas, you can inline inside `ifdef`/`ifndef` (still dual-guarded):

```asciidoc
ifndef::env-github[]
latexmath:[e^{i\pi} + 1 = 0]
endif::[]
ifdef::env-github[]
$e^{i\pi} + 1 = 0$
endif::[]
```

## FAQ

**Q: Can I write text shared across both environments and only wrap the math?**
A: Yes! The surrounding text goes outside the guards:

```asciidoc
根据贝叶斯定理：
ifndef::env-github[]
latexmath:[P(A|B) = \frac{P(B|A)P(A)}{P(B)}]
endif::[]
ifdef::env-github[]
$P(A|B) = \frac{P(B|A)P(A)}{P(B)}$
endif::[]
```

**Q: What if my formula contains `]` or `[` characters?**
A: In `latexmath:[]`, escape them with backslash: `latexmath:[\mathbf{x}_{k+1} = \mathbf{x}_k - [\nabla^2 f(\mathbf{x}_k)\]^{-1}]`.

**Q: Can I check the GitHub rendering locally?**
A: No easy way. Push to a branch and check the rendered `.asc` file on GitHub.
