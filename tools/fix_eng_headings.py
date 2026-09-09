# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
import re

path = os.path.join("ai", "deep-learning", "engineering.asc")
with io.open(path, encoding="utf-8", newline="") as f:
    raw = f.read()
newline = u"\r\n" if u"\r\n" in raw else u"\n"
lines = raw.splitlines(True)


def demote(line):
    if re.match(r"^==+ ", line):
        return u"=" + line
    return line


body = u"".join(demote(line) for line in lines)
if not body.startswith(u"=== Builder's Guide"):
    raise SystemExit("unexpected first heading after demote")
text = u"== Engineering" + newline + body
with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("ok")
