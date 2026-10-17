#!/usr/bin/env python3
"""Validate the hand-written study data in <workdir> before building the page.

usage: python3 check.py <workdir>             validate scenes.json / annotations.json / ipa.json
       python3 check.py <workdir> --ipa-todo  also write ipa_todo.json: the items that need IPA

Exit code 1 when there are errors (things build.py cannot place). Warnings are worth a look but don't block.
"""
import json
import os
import re
import sys

TYPES = {"phrase", "word", "slang", "culture"}


def load(work, name, default=None):
    p = os.path.join(work, name)
    if not os.path.exists(p):
        return default
    return json.load(open(p, encoding="utf-8"))


def needs_ipa(a):
    return a["type"] == "word" or len(a["span"].replace("-", " ").split()) <= 2


def main():
    work = sys.argv[1]
    sents = load(work, "sents.json")
    by_i = {x["i"]: x["en"] for x in sents}
    order = [x["i"] for x in sents]
    errors, warns = [], []
    for x in sents:
        if re.search(r"[\[\]♪]|\([^)]*\)", x["en"]):
            warns.append(f'#{x["i"]}: contains a sound/speaker tag — fix fetch.py\'s TAG pattern or drop the sentence: {x["en"][:60]}')

    scenes = load(work, "scenes.json")
    if not scenes:
        errors.append("scenes.json missing or empty")
    else:
        starts = [s.get("start") for s in scenes]
        if starts[0] != order[0]:
            errors.append(f"first scene must start at sentence {order[0]} (got {starts[0]})")
        for k, s in enumerate(scenes):
            if s.get("start") not in by_i:
                errors.append(f"scene {k + 1}: start {s.get('start')} is not a sentence number")
            if not s.get("title") or not s.get("summary"):
                errors.append(f"scene {k + 1}: needs title and summary")
            if len(s.get("title", "")) > 14:
                warns.append(f"scene {k + 1}: title is {len(s['title'])} chars (guide: <= 14)")
        pos = [order.index(s) for s in starts if s in by_i]
        if pos != sorted(pos) or len(set(pos)) != len(pos):
            errors.append("scene starts must be strictly increasing")

    ann = load(work, "annotations.json", {})
    if isinstance(ann, list):  # list of chunks
        items = [a for c in ann for a in c.get("annotations", [])]
        cors = [c for ch in ann for c in ch.get("corrections", [])]
    else:
        items, cors = ann.get("annotations", []), ann.get("corrections", [])
    if not items:
        errors.append("annotations.json has no annotations")

    seen, per_sent = {}, {}
    for a in items:
        tag = f'#{a.get("i")} "{a.get("span")}"'
        if a.get("type") not in TYPES:
            errors.append(f"{tag}: type must be one of {sorted(TYPES)}")
        text = by_i.get(a.get("i"))
        if text is None:
            errors.append(f"{tag}: no such sentence (dropped?)")
            continue
        k = text.find(a.get("span", "\0"))
        if k < 0:
            errors.append(f"{tag}: span not found verbatim in sentence: {text}")
            continue
        for b in per_sent.get(a["i"], []):
            if not (k + len(a["span"]) <= b[0] or k >= b[1]):
                errors.append(f"{tag}: overlaps another annotation in the same sentence")
        per_sent.setdefault(a["i"], []).append((k, k + len(a["span"])))
        key = a["span"].lower()
        if key in seen:
            warns.append(f"{tag}: same span already annotated at #{seen[key]} (later one is skipped)")
        seen.setdefault(key, a["i"])
        if len(a.get("zh", "")) > 16:
            warns.append(f"{tag}: zh is {len(a['zh'])} chars (guide: <= 16) — keep it a short gloss")
        if len(a.get("note", "")) > 45:
            warns.append(f"{tag}: note is {len(a['note'])} chars (guide: <= 45)")
        if len(a["span"].split()) > 8:
            warns.append(f"{tag}: span is long — highlight the expression, not a whole clause")
        if re.search(r"/[^/]*[ˈˌːəɪʊæɑɔʌɚɝθðʃʒŋ][^/]*/", a.get("note", "")) and " vs " not in a.get("note", ""):
            warns.append(f"{tag}: note contains IPA — fine for a contrast (A /x/ vs B /y/), otherwise it belongs in ipa.json")
    for i, spans in per_sent.items():
        if len(spans) > 2:
            warns.append(f"#{i}: {len(spans)} annotations in one sentence (aim for at most 2)")

    for c in cors:
        tag = f'correction #{c.get("i")} "{c.get("span")}"'
        text = by_i.get(c.get("i"))
        if text is None or c.get("span", "\0") not in text:
            errors.append(f"{tag}: span not found verbatim in sentence")
            continue
        k = text.find(c["span"])
        if any(not (k + len(c["span"]) <= a or k >= b) for a, b in per_sent.get(c["i"], [])):
            errors.append(f"{tag}: overlaps an annotation — narrow the correction span (e.g. ' This here' -> '. This here')")

    ipa = load(work, "ipa.json")
    todo = []
    first = {}
    for a in items:
        first.setdefault(a["span"].lower(), a)
    for a in first.values():
        if needs_ipa(a):
            todo.append({"span": a["span"], "type": a["type"], "zh": a.get("zh", ""), "sentence": by_i.get(a["i"], "")})
    if ipa is not None:
        have = {x["span"].lower(): x["ipa"] for x in ipa}
        miss = [t["span"] for t in todo if t["span"].lower() not in have]
        if miss:
            warns.append(f"ipa.json is missing {len(miss)} item(s): {', '.join(miss[:12])}")
        for span, v in have.items():
            if not (v.startswith("/") and v.endswith("/")):
                errors.append(f'ipa "{span}": write it between slashes, e.g. /duːˈveɪ/')
            if re.search(r"ɒ|əʊ|eə|ɪə|ʊə|t̬|\.", v):
                warns.append(f'ipa "{span}" {v}: British vowel, flap mark or syllable dot — the guide uses General American without dots')
    if "--ipa-todo" in sys.argv:
        json.dump(todo, open(os.path.join(work, "ipa_todo.json"), "w"), ensure_ascii=False, indent=1)
        print(f"wrote ipa_todo.json ({len(todo)} items)")

    counts = {t: sum(1 for a in first.values() if a["type"] == t) for t in sorted(TYPES)}
    dens = len(first) / max(len(sents), 1)
    print(f"{len(sents)} sentences · {len(scenes or [])} scenes · {len(first)} unique annotations "
          f"({dens:.2f}/sentence) {counts} · {len(cors)} corrections")
    if dens < 0.3:
        warns.append("annotation density is low (< 0.3 per sentence)")
    if dens > 0.9:
        warns.append("annotation density is high (> 0.9 per sentence) — the page will feel cluttered")
    for w in warns:
        print("WARN  " + w)
    for e in errors:
        print("ERROR " + e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


main()
