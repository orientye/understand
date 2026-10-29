# -*- coding: utf-8 -*-
import io, os, urllib.request
base = "https://labuladong.online/algo-visualize/static/js/"
chunks = [
    "996.17800b2f.chunk.js",
    "55.a671516d.chunk.js",
    "873.e6fd136b.chunk.js",
    "266.f5a1dcce.chunk.js",
    "966.34a8f329.chunk.js",
    "21.b5561ce2.chunk.js",
    "501.20eec8d7.chunk.js",
    "528.d59225a9.chunk.js",
]
outdir = os.path.join(os.environ["TEMP"], "vizchunks")
os.makedirs(outdir, exist_ok=True)
needles = [
    "createDirectedGraph", "@visualize", "PROGRAM", "/viz/run",
    "acorn", "esprima", "interpreter", "bfs", "Graph",
    "getContext", "svg", "canvas", "d3", "G6", "@antv",
    "layout", "forceSimulation", "adjacency",
]
for name in chunks:
    path = os.path.join(outdir, name)
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        url = base + name
        print("GET", name)
        urllib.request.urlretrieve(url, path)
    data = io.open(path, encoding="utf-8", errors="replace").read()
    hits = [n for n in needles if n in data]
    print(f"{name:28} {len(data):8} hits={hits}")
