---
name: youtube-english-study
description: 把一个 YouTube 视频做成单文件的「英语精读本」HTML：英文字幕按句重排、按场景分段配中文导读，有用的短语/生词/俚语/文化点直接在原文里高亮并标中文意思，带美式音标、点读发音（含慢速）、跳转原视频原声、遮住中文自测、已掌握打勾和短语总表。只要用户发来 YouTube 链接（youtube.com/watch、youtu.be、/shorts/）并提到英文学习、英语学习、学英语、练英语、精读、精读本、用这个视频学英语、做成双语/中英对照学习材料，就使用本技能，即使用户没说"HTML"或"精读本"。Use whenever the user shares a YouTube link and wants to study/learn English from it (bilingual study page, phrase highlights, vocabulary, pronunciation). Not for just summarizing a video, burning subtitles into a video, or downloading it.
---

# YouTube → 英语精读本

Turn one YouTube video into a single self-contained HTML page the user opens by double-clicking. They read the
English transcript scene by scene, see useful expressions highlighted inline with Chinese glosses, tap to hear
pronunciation, jump to the video at any sentence, and quiz themselves. This was designed with the user over a
long session; the scripts reproduce the exact page they approved, so stick to them instead of improvising HTML.

Skill dir: `~/.claude/skills/youtube-english-study` (scripts in `scripts/`, page template in `assets/`,
annotation rules in `references/annotation-guide.md` — read that file before writing annotations).

## Ground rules (why the page looks the way it does)

- **No full translation.** The transcript is the creator's work. The Chinese layer is a short guide per scene plus
  glosses for highlighted expressions — never a sentence-by-sentence translation, in the page or in chat. If the
  user asks for a full line-by-line translation, explain this briefly and point them to YouTube's own auto-translated
  subtitles. Likewise don't paste the transcript into the chat.
- **Private, local file.** Save it to disk only. Don't publish it as an Artifact or upload it anywhere.
- **Correctness over volume.** A wrong gloss or wrong IPA teaches the user something false. Fewer, accurate
  highlights beat many sloppy ones; verify before building.

## Where things go

- **Work dir** (intermediate files): fetch.py creates `<parent>/jingdu-<videoId>/` — pass your scratchpad
  (or `$TMPDIR`) as `<parent>` and use the `work:` path it prints for every later step.
- **Output dir**: the folder the user names; otherwise `~/Vibe Coding Demo/Agent Reach/` (where the user keeps
  these pages); if that doesn't exist, the current working directory. The file is named `<video title>-英语精读本.html`
  and regenerating the same video overwrites it (the user's ✓ progress survives — it's stored per video id).

## Steps

Run the scripts with `python3 -I` and pass paths as arguments.

### 1. Fetch subtitles

```bash
python3 -I ~/.claude/skills/youtube-english-study/scripts/fetch.py "<url>" <parent>
```

It accepts any YouTube link form (watch?v=, youtu.be/, /shorts/, /live/), picks official English subtitles if
they exist (best), otherwise YouTube's auto captions, strips sound/speaker tags ((upbeat music), [Applause], ♪, >>),
and writes `meta.json`, `sents.json`, `sents.tsv` (number · time · sentence) and `suspects.json` into the work
dir it prints first. Read its printout:

- **Suspects** are likely caption artifacts: a cut-off copy of the next sentence, an exact repeat, a stray lowercase
  scrap, a leftover sound tag. Look at each in context in `sents.tsv` and drop only real artifacts — a speaker
  deliberately repeating a word ("Substitute. … Substitute.") or a sentence that merely starts in lowercase stays.
  `python3 -I …/scripts/drop.py <work> 127 155 …`. If a sound tag survived inside a real sentence, the TAG pattern
  in fetch.py missed a format — extend it and re-run fetch.py rather than leaving the tag in the learner's text.
- **Auto captions without punctuation** come out as lines split at pauses. That's fine; mention it in the final
  report. If auto captions are the only option the transcript may have recognition errors — fix only the ones you
  are sure of (corrections).
- **No English subtitles at all** → stop and tell the user this video can't be made into a 精读本 (no transcript).
- **yt-dlp missing / HTTP 429** → the script says so. For 429 wait a minute and retry once; if it persists, tell the user.
- Long videos (> ~40 min, > ~500 sentences) work but take a while — tell the user up front, then proceed.

### 2. Read the whole transcript, then write `scenes.json`

Read all of `sents.tsv` first — you can't split scenes or pick good expressions without knowing the content.
Then write `scenes.json` (format and rules: guide §1).

### 3. Write `annotations.json`

Highlights + corrections, following guide §2 closely (exact spans, ≤ 2 per sentence, ~0.4–0.7 per sentence,
short in-context Chinese glosses, optional notes). For more than ~120 sentences split the work by scene groups
and verify each group (guide §4).

### 4. Write `ipa.json`

```bash
python3 -I ~/.claude/skills/youtube-english-study/scripts/check.py <work> --ipa-todo
```

Then transcribe every item in `ipa_todo.json` (conventions: guide §3) and re-check the list once for British
vowels, stress and endings.

### 5. Validate, fix, build

```bash
python3 -I ~/.claude/skills/youtube-english-study/scripts/check.py <work>
python3 -I ~/.claude/skills/youtube-english-study/scripts/build.py <work> "<output dir>"
```

Fix every `ERROR` from check.py (usually a span not copied exactly, or a correction overlapping a highlight) and
read the `WARN`s. build.py prints counts, any `NOT PLACED` items (fix and rebuild), and the output path last.

### 6. Look at it

If a browser tool is available, serve the output folder (`python3 -m http.server --directory "<output dir>"` via the
preview tool, or open the file) and check once at desktop and phone width: a scene with highlights, a tap on a
highlight (popover with IPA + 朗读), and the 短语总表. Opening the HTML from disk also works for the user — no
server needed. Without a working browser tool, at least compare the counts build.py printed with what you wrote,
and if `node` exists, syntax-check the page script (extract the last `<script>` block and run `node --check`).

### 7. Publish to GitHub

The user has standing authorization to upload every finished page to their public repo
`Jalensuggs/youtube-english-study`, so do this without asking:

```bash
python3 -I ~/.claude/skills/youtube-english-study/scripts/publish.py "<the html path>"
```

It uploads to `pages/` via the gh CLI (no clone) and prints the file's GitHub URL — include that in the report.
If gh is missing or logged out the script says so and exits; don't try another route, just mention it in the
report and leave the local file as the deliverable. Only this page gets published: never upload the work dir,
subtitle files, or anything else.

## Report to the user (in Chinese, short)

- Path of the HTML as a clickable link, and that they can double-click it to open in a browser.
- The GitHub URL from step 7 (or that publishing was skipped and why).
- Video title, duration, number of scenes, number of highlights by type, number of corrections, how many have IPA.
- The subtitle source: official subtitles, or auto captions (and if unpunctuated, that lines are split at pauses).
- Anything uncertain (e.g. a correction that is a guess) and anything you dropped.
- One line on how to use it: 中英标注 / 遮住中文 / 纯英文, tap highlights for 发音和用法, 时间戳跳原视频, 文末短语总表打勾。
