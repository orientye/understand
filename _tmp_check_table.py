# -*- coding: utf-8 -*-
import io
import sys
import unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def dw(s):
    w = 0
    for ch in s:
        e = unicodedata.east_asian_width(ch)
        if e in ("F", "W"):
            w += 2
        elif unicodedata.category(ch) == "So":
            w += 2
        else:
            w += 1
    return w


path = r"c:\orient\my\understand\ai\deep-learning.asc"
with io.open(path, encoding="utf-8") as f:
    lines = f.readlines()

# table is around 721-728 (1-indexed)
print("=== table display widths ===")
for i in range(720, 728):
    s = lines[i].rstrip("\n")
    print("%d  dw=%d  len=%d" % (i + 1, dw(s), len(s)))
    parts = s.split("│")
    if len(parts) > 1:
        print("    cells dw:", [dw(p) for p in parts])
        print("    cells repr:", [p for p in parts])

print()
print("=== targeted checks ===")
sec = "".join(lines[675:773])
print("has u_xtep (wrong):", "uₓₜₑₚ" in sec)
print("has u_step (right):", "uₛₜₑₚ" in sec)
print("has mixed parallele:", "∥" in sec[sec.find("方向导数"):sec.find("③")])
print("has stationarity new wording:", "满足 ∇f(x) = 0 的点称为驻点" in sec)
print("has bottom border:", "└" in sec and "┘" in sec)
print("has extra space before top-right:", "─── ┐" in sec)

# remaining ∥ in this section
for i, line in enumerate(lines[675:773], start=676):
    if "∥" in line:
        print("remaining ∥ at line", i, ":", line.strip())
    if "uₓ" in line:
        print("remaining uₓ at line", i)
