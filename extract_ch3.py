import io
with io.open(r"d:\book\ai\build-reasoning-model-scratch.txt", encoding="utf-8") as f:
    lines = f.readlines()
start = 2760 - 1
end = 4291 - 1
out = "".join(lines[start:end])
with io.open(r"c:\orient\my\understand\ch3_part2.txt", "w", encoding="utf-8") as g:
    g.write(out)
print("done", len(out), "chars")
