#!/usr/bin/env python3
"""Build the single-file English study page (英语精读本) from a work dir.

usage: python3 build.py <workdir> <output-dir>

Reads <workdir>/meta.json, sents.json, scenes.json, annotations.json and (optional) ipa.json,
fills ../assets/template.html and writes "<video title>-英语精读本.html" into <output-dir>.
Prints the output path on the last line.
"""
import html
import json
import os
import re
import sys

TYPES = {
    "phrase": "实用短语",
    "word": "生词",
    "slang": "口语俚语",
    "culture": "文化词源",
}

SPEAKER_SVG = (
    '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M11 5 6 9H3v6h3l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>'
    '<path d="M18.5 5.5a9 9 0 0 1 0 13"/></svg>'
)


def esc(s):
    return html.escape(str(s), quote=True)


def mmss(t):
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def say_text(a):
    """What the speech engine reads: an explicit "say", else spell out short acronyms (POV -> P.O.V.)."""
    if a.get("say"):
        return a["say"]
    return re.sub(r"\b([A-Z]{2,3})\b", lambda m: ".".join(m.group(1)) + ".", a["span"])


def load(work, name, default=None):
    p = os.path.join(work, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def place(text, items):
    """First non-overlapping occurrence of each item's span in text."""
    placed = []
    for it in items:
        start = 0
        while True:
            k = text.find(it["span"], start)
            if k < 0:
                break
            end = k + len(it["span"])
            if all(end <= a or k >= b for a, b, _ in placed):
                placed.append((k, end, it))
                break
            start = k + 1
    return placed


def render_sentence(sent, anns, cors, missed):
    text = sent["en"]
    marks = [(a, b, ("ann", it)) for a, b, it in place(text, anns)]
    taken = [(a, b) for a, b, _ in marks]
    for a, b, it in place(text, cors):
        if all(b <= x or a >= y for x, y in taken):
            marks.append((a, b, ("cor", it)))
    found = {id(m[2][1]) for m in marks}
    for kind, group in (("ann", anns), ("cor", cors)):
        for it in group:
            if id(it) not in found:
                missed.append((sent["i"], it["span"], kind))
    marks.sort(key=lambda m: m[0])
    out, pos = [], 0
    for a, b, (kind, it) in marks:
        out.append(esc(text[pos:a]))
        span = esc(text[a:b])
        if kind == "ann":
            out.append(
                f'<span class="hl t-{it["type"]}" id="p{it["pid"]}" data-pid="{it["pid"]}"'
                f' tabindex="0" data-note="{esc(it.get("note") or "")}" data-type="{TYPES[it["type"]]}"'
                f' data-ipa="{esc(it.get("ipa", ""))}" data-say="{esc(say_text(it))}">'
                f'<span class="en">{span}</span>'
                f'<span class="zh">{esc(it["zh"])}</span></span>'
            )
        else:
            out.append(
                f'<span class="fix" tabindex="0" data-orig="{span}" data-note="{esc(it.get("note", ""))}">'
                f'{esc(it["fix"])}</span>'
            )
        pos = b
    out.append(esc(text[pos:]))
    return "".join(out)


def safe_name(title):
    t = re.sub(r'[\\/:*?"<>|#%{}^~\[\]`]+', " ", title)
    t = re.sub(r"\s+", " ", t).strip(" .")
    if len(t) > 90:
        cut = t[:90]
        t = cut[:cut.rfind(" ")] if " " in cut[30:] else cut
        prev = None
        while prev != t:  # don't end on a dangling "by", "in", "the", "-" ...
            prev = t
            t = re.sub(r"\s+(by|in|of|the|a|an|and|or|to|for|with|on|at|from|vs|&|-|–|\|)$", "", t, flags=re.I)
    return t.rstrip(" .-|") or "video"


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    work, out_dir = sys.argv[1], sys.argv[2]
    meta = load(work, "meta.json")
    sents = load(work, "sents.json")
    scenes = load(work, "scenes.json")
    ann = load(work, "annotations.json", {})
    ipa = {x["span"].lower(): x["ipa"] for x in load(work, "ipa.json", [])}
    chunks = ann if isinstance(ann, list) else [ann]
    video_url = meta["url"]

    by_sent_ann, by_sent_cor, seen, pid = {}, {}, set(), 0
    for ch in chunks:
        for a in ch.get("annotations", []):
            if a.get("type") not in TYPES or a["span"].lower() in seen:
                continue
            seen.add(a["span"].lower())
            pid += 1
            a["pid"] = pid
            if a["span"].lower() in ipa:
                a["ipa"] = ipa[a["span"].lower()]
            by_sent_ann.setdefault(a["i"], []).append(a)
        for c in ch.get("corrections", []):
            by_sent_cor.setdefault(c["i"], []).append(c)

    # scene k covers sentences from its start up to the next scene's start
    order = [s["i"] for s in sents]
    bounds = [order.index(s["start"]) for s in scenes] + [len(sents)]

    missed, scene_html, index_rows, nav = [], [], [], []
    counts = {k: 0 for k in TYPES}
    for k, sc in enumerate(scenes):
        ss = sents[bounds[k]:bounds[k + 1]]
        if not ss:
            continue
        t0 = ss[0]["t"]
        t1 = sents[bounds[k + 1]]["t"] if bounds[k + 1] < len(sents) else meta["duration"]
        lines = []
        for s in ss:
            anns = by_sent_ann.get(s["i"], [])
            body = render_sentence(s, anns, by_sent_cor.get(s["i"], []), missed)
            sec = int(s["t"])
            lines.append(
                f'<p class="line" id="s{s["i"]}">'
                f'<a class="ts" href="{video_url}&amp;t={sec}s" target="_blank" rel="noopener" '
                f'title="在 YouTube 从 {mmss(sec)} 开始播放">{mmss(sec)}</a>'
                f'<span class="txt">{body}</span></p>'
            )
            for a in anns:
                if (s["i"], a["span"], "ann") in missed:
                    continue
                counts[a["type"]] += 1
                index_rows.append((k, a, sec))
        n = k + 1
        chip = re.split(r"[:：,，、]", sc["title"])[0].strip()
        chip = chip if len(chip) <= 14 else chip[:13] + "…"
        nav.append(f'<a href="#scene{n}" class="chip"><b>{n}</b>{esc(chip)}</a>')
        scene_html.append(
            f'<section class="scene" id="scene{n}">'
            f'<header class="scene-head"><div class="scene-meta">'
            f'<span class="scene-no">场景 {n:02d}</span>'
            f'<a class="scene-time" href="{video_url}&amp;t={int(t0)}s" target="_blank" rel="noopener">'
            f'{mmss(t0)} – {mmss(t1)}</a></div>'
            f'<h2>{esc(sc["title"])}</h2><p class="guide"><span class="guide-tag">中文导读</span>{esc(sc["summary"])}</p>'
            f'</header><div class="lines">{"".join(lines)}</div></section>'
        )

    idx = []
    for k, sc in enumerate(scenes):
        rows = [(a, t) for s, a, t in index_rows if s == k]
        if not rows:
            continue
        lis = "".join(
            f'<li class="t-{a["type"]}" data-pid="{a["pid"]}">'
            f'<button class="learned" aria-label="标记已掌握" title="标记已掌握"></button>'
            f'<div class="ix-main"><a href="#p{a["pid"]}" class="ix-en">{esc(a["span"])}</a>'
            + (f'<span class="ipa">{esc(a["ipa"])}</span>' if a.get("ipa") else "")
            + f'</div>'
            f'<button class="say" data-say="{esc(say_text(a))}" '
            f'aria-label="朗读 {esc(a["span"])}" title="朗读">{SPEAKER_SVG}</button>'
            f'<span class="ix-zh">{esc(a["zh"])}</span>'
            f'<span class="ix-meta"><span class="ix-type">{TYPES[a["type"]]}</span>'
            f'<a class="orig" href="{video_url}&amp;t={t}s" target="_blank" rel="noopener" '
            f'title="在 YouTube 听原声">▶ 原声 {mmss(t)}</a></span></li>'
            for a, t in rows
        )
        idx.append(f'<div class="ix-scene"><h3>{k + 1:02d} · {esc(sc["title"])}</h3><ul>{lis}</ul></div>')

    total = sum(counts.values())
    legend = "".join(
        f'<label class="lg t-{k}"><input type="checkbox" data-type="{k}" checked>'
        f'<span class="sw"></span>{v} <em>{counts[k]}</em></label>'
        for k, v in TYPES.items()
    )
    if meta.get("source") == "manual":
        source_note = "英文原文来自该视频的英文字幕，已按完整句子重新断句，并去掉了（音乐）（掌声）这类音效标注。"
    elif meta.get("punctuated"):
        source_note = "英文原文来自 YouTube 自动生成的字幕，已按句子断句；自动字幕个别词可能识别有误。"
    else:
        source_note = "英文原文来自 YouTube 自动生成的字幕。自动字幕没有标点，这里按说话的停顿分行；个别词可能识别有误。"
    n_cor = sum(len(v) for v in by_sent_cor.values()) - sum(1 for m in missed if m[2] == "cor")
    fix_note = ("带红色虚线和 ✎ 的地方是原字幕写错、已经改正的位置（错字、品牌名、漏掉的标点），"
                "点一下能看原字幕写的是什么。") if n_cor else ""
    unit = "句" if meta.get("source") == "manual" or meta.get("punctuated") else "行"

    here = os.path.dirname(os.path.abspath(__file__))
    tpl = open(os.path.join(here, "..", "assets", "template.html"), encoding="utf-8").read()
    rep = {
        "{{TITLE}}": esc(meta["title"]),
        "{{CHANNEL}}": esc(meta.get("channel") or "YouTube"),
        "{{DURATION}}": mmss(meta["duration"]),
        "{{VIDEO_URL}}": esc(video_url),
        "{{STORE_KEY}}": "jingdu-" + re.sub(r"[^A-Za-z0-9_-]", "", meta["id"]),
        "{{NSENT}}": str(len(sents)),
        "{{UNIT}}": unit,
        "{{TOTAL}}": str(total),
        "{{SOURCE_NOTE}}": esc(source_note),
        "{{FIX_NOTE}}": esc(fix_note),
        "{{LEGEND}}": legend,
        "{{NAV}}": "".join(nav),
        "{{SCENES}}": "".join(scene_html),
        "{{INDEX}}": "".join(idx),
    }
    page = tpl
    for k, v in rep.items():
        page = page.replace(k, v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        sys.exit(f"template placeholders not filled: {sorted(set(left))}")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f'{safe_name(meta["title"])}-英语精读本.html')
    open(out, "w", encoding="utf-8").write(page)
    n_ipa = sum(1 for _, a, _ in index_rows if a.get("ipa"))
    print(f"{len(sents)} {unit} · {len(scenes)} scenes · {total} highlights {counts} · "
          f"{n_cor} corrections · {n_ipa} with IPA")
    if missed:
        print("NOT PLACED (fix with check.py):", missed)
    print(out)


main()
