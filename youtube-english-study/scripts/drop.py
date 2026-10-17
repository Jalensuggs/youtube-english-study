#!/usr/bin/env python3
"""Remove caption-artifact sentences (by number) from <workdir>/sents.json and sents.tsv.

usage: python3 drop.py <workdir> 127 155 156 ...

Sentence numbers are kept as-is (no renumbering), so do this before writing scenes/annotations.
"""
import json
import os
import sys

work, nums = sys.argv[1], {int(x) for x in sys.argv[2:]}
p = os.path.join(work, "sents.json")
sents = json.load(open(p, encoding="utf-8"))
keep = [x for x in sents if x["i"] not in nums]
gone = [x for x in sents if x["i"] in nums]
json.dump(keep, open(p, "w"), ensure_ascii=False, indent=0)
with open(os.path.join(work, "sents.tsv"), "w", encoding="utf-8") as f:
    for x in keep:
        m, s = divmod(int(x["t"]), 60)
        h, m = divmod(m, 60)
        ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        f.write(f'{x["i"]}\t{ts}\t{x["en"]}\n')
for x in gone:
    print(f'dropped #{x["i"]}: {x["en"]}')
print(f"{len(keep)} sentences left")
