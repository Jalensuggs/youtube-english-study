#!/usr/bin/env python3
"""Download a YouTube video's English subtitles and turn them into numbered sentences.

usage: python3 fetch.py <youtube-url> <parent-dir> [--prefer manual|auto]

Creates <parent-dir>/jingdu-<videoId>/ (the work dir), prints "work: <path>" first, and writes:
  meta.json      video id, title, channel, duration, subtitle source
  sents.json     [{"i": 1, "t": 0.1, "en": "..."}]   (t = start seconds)
  sents.tsv      i <TAB> m:ss <TAB> text   -- the file to read when planning scenes/annotations
  suspects.json  sentence numbers that look like caption artifacts (duplicates / stray fragments)
"""
import json
import os
import re
import subprocess
import sys
import time


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def ytdlp(args, retries=2):
    for attempt in range(retries + 1):
        p = subprocess.run(["yt-dlp", *args], capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout
        if "429" in p.stderr and attempt < retries:
            time.sleep(6 * (attempt + 1))
            continue
        die("yt-dlp failed:\n" + p.stderr.strip()[-1500:])


def mmss(t):
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# non-speech tags in any case: [Music], [Applause], (APPLAUSE), (upbeat music), (Laughter), ♪ lyrics ♪
TAG = re.compile(r"\[[^\]]*\]|\((?=[^)]*[A-Za-z])[^()]{1,40}\)|♪+[^♪]*♪+|♪")


def pick_track(info, prefer):
    manual = {k: v for k, v in (info.get("subtitles") or {}).items()
              if re.match(r"^en([-_].*)?$", k) and k != "live_chat"}
    auto = {k: v for k, v in (info.get("automatic_captions") or {}).items()
            if k in ("en-orig", "en")}
    def best(d, order):
        for k in order:
            if k in d:
                return k
        return sorted(d)[0] if d else None
    m = best(manual, ["en-US", "en", "en-GB", "en-CA", "en-AU"])
    a = best(auto, ["en-orig", "en"])
    if prefer == "auto" and a:
        return "auto", a
    if m:
        return "manual", m
    if a:
        return "auto", a
    return None, None


# ---------- manual subtitles (.srt): punctuated, cut by time -> rebuild sentences ----------

def sec(t):
    h, m, r = t.strip().split(":")
    s, ms = r.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(path):
    raw = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").strip().split("\n\n")
    words = []
    for blk in raw:
        ls = blk.split("\n")
        k = next((j for j, l in enumerate(ls) if "-->" in l), None)
        if k is None:
            continue
        a, b = [sec(x) for x in ls[k].split("-->")]
        text = re.sub(r"<[^>]+>", "", " ".join(ls[k + 1:]))
        text = TAG.sub(" ", text)
        text = re.sub(r"^\s*>>\s*|\s>>\s", " ", text)  # speaker-change markers
        ws = text.split()
        for j, w in enumerate(ws):
            words.append((w, a + (b - a) * j / max(len(ws), 1)))
    return words


def is_end(w):
    return bool(re.search(r'[.?!]["”\')]*$', w)) and not re.fullmatch(r"(Mr|Mrs|Ms|Dr|St|vs|etc)\.", w)


def by_sentence(words):
    sents, cur, t0 = [], [], None
    for w, t in words:
        if t0 is None:
            t0 = t
        cur.append(w)
        if is_end(w) or len(cur) >= 60:
            sents.append((t0, " ".join(cur)))
            cur, t0 = [], None
    if cur:
        sents.append((t0, " ".join(cur)))
    return sents


def by_pause(words):
    """Unpunctuated auto captions: break at speech pauses, but keep lines readable (>= ~6 words)."""
    lines, cur = [], []
    for w, t in words:
        if cur:
            gap, n = t - cur[-1][1], len(cur)
            if (gap >= 1.2 and n >= 3) or (gap >= 0.5 and n >= 6) or (gap >= 0.25 and n >= 14) or n >= 24:
                lines.append(cur)
                cur = []
        cur.append((w, t))
    if cur:
        lines.append(cur)
    return [(ln[0][1], " ".join(w for w, _ in ln)) for ln in lines]


def punctuated(words):
    return sum(is_end(w) for w, _ in words) >= max(3, len(words) * 0.02)


# ---------- auto captions (.json3): word-level timings ----------

def parse_json3(path):
    data = json.load(open(path, encoding="utf-8"))
    words = []
    for ev in data.get("events", []):
        if "segs" not in ev or ev.get("aAppend"):
            continue
        base = ev.get("tStartMs", 0)
        for sg in ev["segs"]:
            w = sg.get("utf8", "").strip()
            if not w or TAG.fullmatch(w) or w == ">>":
                continue
            words.append((w, (base + sg.get("tOffsetMs", 0)) / 1000))
    words.sort(key=lambda x: x[1])
    return words


def norm(s):
    return re.sub(r"[^a-z0-9' ]", "", s.lower()).split()


def find_suspects(sents):
    """Caption artifacts: repeated fragments and stray lowercase scraps. Claude reviews these."""
    sus = []
    for k, x in enumerate(sents):
        w = norm(x["en"])
        why = None
        prev = [norm(y["en"]) for y in sents[max(0, k - 2):k]]
        nxt = [norm(y["en"]) for y in sents[k + 1:k + 3]]
        if re.search(r"[\[\]♪]|\([^)]*\)", x["en"]):
            why = "contains a leftover sound/speaker tag"
        elif w and w in prev:
            why = "repeats a sentence just before it"
        elif len(w) >= 3 and any(len(n) > len(w) and n[:4] == w[:4] for n in nxt):
            why = "starts like a longer sentence right after it (likely a cut-off duplicate)"
        elif x["en"][:1].islower() and len(w) <= 6:
            why = "short fragment starting in lowercase"
        if why:
            sus.append({"i": x["i"], "t": mmss(x["t"]), "en": x["en"], "why": why})
    return sus


def main():
    if len(sys.argv) < 3:
        die(__doc__)
    url, parent = sys.argv[1], sys.argv[2]
    prefer = sys.argv[sys.argv.index("--prefer") + 1] if "--prefer" in sys.argv else "manual"
    if subprocess.run(["which", "yt-dlp"], capture_output=True).returncode != 0:
        die("yt-dlp is not installed. Install it with:  brew install yt-dlp   (or: uv tool install yt-dlp)")

    info = json.loads(ytdlp(["-J", "--skip-download", "--no-warnings", url]))
    vid = info["id"]
    work = os.path.join(parent, "jingdu-" + re.sub(r"[^A-Za-z0-9_-]", "", vid))
    os.makedirs(work, exist_ok=True)
    print(f"work:     {work}")
    kind, lang = pick_track(info, prefer)
    if not kind:
        die(f"This video has no English subtitles or auto captions (video id {vid}).")

    for f in os.listdir(work):
        if f.startswith("sub."):
            os.remove(os.path.join(work, f))
    fmt = "srt" if kind == "manual" else "json3"
    flag = "--write-subs" if kind == "manual" else "--write-auto-subs"
    ytdlp(["--skip-download", flag, "--sub-langs", lang, "--sub-format", fmt,
           "--no-warnings", "-o", os.path.join(work, "sub"), f"https://www.youtube.com/watch?v={vid}"])
    files = [f for f in os.listdir(work) if f.startswith("sub.") and f.endswith("." + fmt)]
    if not files:
        die(f"Subtitle download produced no .{fmt} file (track {lang}). YouTube may be rate-limiting; try again in a few minutes.")
    path = os.path.join(work, files[0])
    words = parse_srt(path) if kind == "manual" else parse_json3(path)
    has_punct = kind == "manual" or punctuated(words)
    raw = by_sentence(words) if has_punct else by_pause(words)
    raw = [(t, s.strip()) for t, s in raw if re.search(r"[A-Za-z]", s)]
    sents = [{"i": k + 1, "t": round(t, 2), "en": s} for k, (t, s) in enumerate(raw)]
    if not sents:
        die("The subtitle file was empty.")

    meta = {
        "id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": info.get("title") or vid,
        "channel": info.get("channel") or info.get("uploader") or "",
        "duration": int(info.get("duration") or sents[-1]["t"] + 5),
        "source": kind,
        "track": lang,
        "punctuated": has_punct,
    }
    json.dump(meta, open(os.path.join(work, "meta.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(sents, open(os.path.join(work, "sents.json"), "w"), ensure_ascii=False, indent=0)
    with open(os.path.join(work, "sents.tsv"), "w", encoding="utf-8") as f:
        for x in sents:
            f.write(f'{x["i"]}\t{mmss(x["t"])}\t{x["en"]}\n')
    sus = find_suspects(sents) if has_punct else []
    json.dump(sus, open(os.path.join(work, "suspects.json"), "w"), ensure_ascii=False, indent=1)

    nwords = sum(len(x["en"].split()) for x in sents)
    unit = "sentences" if has_punct else "lines (no punctuation, split at pauses)"
    print(f'title:    {meta["title"]}')
    print(f'channel:  {meta["channel"]}   duration: {mmss(meta["duration"])}')
    print(f'subtitle: {kind} ({lang})   ->  {len(sents)} {unit}, {nwords} words')
    print(f'suspects: {len(sus)}' + ("" if not sus else "  (review with suspects.json, drop real artifacts with drop.py)"))
    for s in sus:
        print(f'  #{s["i"]} [{s["t"]}] {s["en"]}   <- {s["why"]}')


main()
