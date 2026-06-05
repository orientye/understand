---
name: math-formula
description: |
  Write AsciiDoc math formulas with dual-environment support (GitHub + non-GitHub).
  Inline: non-GitHub uses stem:[], GitHub uses $ $.
  Block: non-GitHub uses [stem]++++, GitHub uses ```math.
trigger: when the user asks about writing math formulas, LaTeX, AsciiMath, or KaTeX in AsciiDoc, or asks for help formatting mathematical expressions in this repo
---

# Writing Math Formulas in AsciiDoc (Dual-Environment)

## The Problem

This repo uses **AsciiDoc (`.asc`)** format. However, **GitHub's AsciiDoc renderer does not support AsciiDoc's native math macros** — it renders them as raw text. To make formulas render correctly on both GitHub (`env-github`) and locally/non-GitHub, you must wrap each formula in `ifdef`/`ifndef` conditional blocks.

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
| Non-GitHub | `stem:[formula]` |
| GitHub | `$formula$` |

### Example

```asciidoc
ifndef::env-github[]
牛顿法搜索方向: stem:[\mathbf{x}_{k+1} = \mathbf{x}_k - [\nabla^2 f(\mathbf{x}_k)]^{-1} \nabla f(\mathbf{x}_k)]
endif::[]
ifdef::env-github[]
牛顿法搜索方向: $\mathbf{x}_{k+1} = \mathbf{x}_k - [\nabla^2 f(\mathbf{x}_k)]^{-1} \nabla f(\mathbf{x}_k)$
endif::[]
```

## Block Formulas

| Environment | Syntax |
|---|---|
| Non-GitHub | `[stem]++++...++++` |
| GitHub | ` ```math ``` ` |

### Example

```asciidoc
ifndef::env-github[]
[stem]
++++
P(B|A) = \frac{P(A \cap B)}{P(A)}
++++
endif::[]
ifdef::env-github[]
```math
P(B|A) = \frac{P(A \cap B)}{P(A)}
```
endif::[]
```

> ⚠️ In non-GitHub, the `\[` and `\]` lines must be separated from text by blank lines, otherwise they may be treated as inline text.

## Common Patterns

### Derivatives

```asciidoc
ifndef::env-github[]
stem:[\frac{dy}{dx} = \lim_{\Delta x \to 0} \frac{\Delta y}{\Delta x}]

[stem]
++++
\int_a^b f(x) \, dx = F(b) - F(a)
++++
endif::[]
ifdef::env-github[]
$\frac{dy}{dx} = \lim_{\Delta x \to 0} \frac{\Delta y}{\Delta x}$

```math
\int_a^b f(x) \, dx = F(b) - F(a)
```
endif::[]
```

### Matrices

```asciidoc
ifndef::env-github[]
[stem]
++++
A = \begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}
++++
endif::[]
ifdef::env-github[]
```math
A = \begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}
```
endif::[]
```

### Summations

```asciidoc
ifndef::env-github[]
stem:[\sum_{i=1}^{n} i = \frac{n(n+1)}{2}]

[stem]
++++
\sigma(x) = \frac{1}{1 + e^{-x}}
++++
endif::[]
ifdef::env-github[]
$\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$

```math
\sigma(x) = \frac{1}{1 + e^{-x}}
```
endif::[]
```

## Common Gotchas

### Inline `stem:[...]` Must Be Wrapped Entirely

`stem:[...]` is **not recognized by GitHub's AsciiDoc renderer**. Any paragraph containing `stem:[...]` must be fully wrapped in `ifndef`/`ifdef`:

```asciidoc
❌ Wrong — GitHub renders `stem:[\mathbf{F}]` as raw text:
设 V 是三维空间中的有界区域...若 stem:[\mathbf{F}] 在 V 上具有连续偏导数，则:

✅ Correct:
设 V 是三维空间中的有界区域...若
ifndef::env-github[]
stem:[\mathbf{F}] 在 V 上具有连续偏导数，则:
endif::[]
ifdef::env-github[]
$\mathbf{F}$ 在 V 上具有连续偏导数，则:
endif::[]
```

This applies to **list items** too:

```asciidoc
❌ Wrong:
* 梯度场: stem:[\mathbf{F} = \nabla f]（势函数的梯度构成一个向量场）

✅ Correct:
ifndef::env-github[]
* 梯度场: stem:[\mathbf{F} = \nabla f]（势函数的梯度构成一个向量场）
endif::[]
ifdef::env-github[]
* 梯度场: $\mathbf{F} = \nabla f$（势函数的梯度构成一个向量场）
endif::[]
```

### Other Rules

- The two blocks MUST be adjacent — do not put text or blank lines between `endif::[]` and `ifdef::env-github[]`.
- For short formulas, you can put surrounding text outside the guards (but the `stem:[...]` part must be inside):

## FAQ

**Q: Can I write text shared across both environments and only wrap the math?**
A: Yes! The surrounding text goes outside the guards:

```asciidoc
根据贝叶斯定理：
ifndef::env-github[]
stem:[P(A|B) = \frac{P(B|A)P(A)}{P(B)}]
endif::[]
ifdef::env-github[]
$P(A|B) = \frac{P(B|A)P(A)}{P(B)}$
endif::[]
```

**Q: What if my formula contains `]` or `[` characters?**
A: In `stem:[]`, escape them with backslash: `stem:[\mathbf{x}_{k+1} = \mathbf{x}_k - [\nabla^2 f(\mathbf{x}_k)\]^{-1}]`.

**Q: Can I check the GitHub rendering locally?**
A: No easy way. Push to a branch and check the rendered `.asc` file on GitHub.
