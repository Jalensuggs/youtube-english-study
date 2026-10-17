# How to write the study data

The page is only as good as these three hand-written files. The reader is a Chinese native speaker at
roughly intermediate level who wants to learn real, spoken English from the video — so every choice below
is about "what would actually help this person read, understand and reuse the English".

All files live in the work dir next to `sents.json` / `sents.tsv` (sentence numbers = first column of `sents.tsv`).

## Contents
1. scenes.json — scene split + Chinese guide
2. annotations.json — inline highlights + subtitle corrections
3. ipa.json — American IPA for words and short phrases
4. Splitting the work for long videos

---

## 1. scenes.json

```json
[
  {"start": 1,  "title": "开场：apartment 这个词哪来的", "summary": "博主在公寓里开场，先讲 apartment 的来历……"},
  {"start": 10, "title": "房间导览和打扫", "summary": "……"}
]
```

- `start` is the sentence number where the scene begins; the first scene starts at the first sentence. Starts must increase.
- Cut where the topic or activity changes — roughly one scene per 1–1.5 minutes of content, at least 3 (≈ 5–7 for an 8-minute video, ~10–12 for 18 minutes; a 1-hour talk ~15–20 with longer scenes). Scenes far shorter than 30 seconds feel choppy.
- `title`: short Chinese, ≤ 14 characters, says what happens ("怎么分辨真丝", "词源小课堂：breakfast"). Put the key idea before any colon or comma — the part before the first `：`/`，` becomes the nav chip.
- `summary`: 2–3 Chinese sentences in your own words: what happens and anything worth noticing (an etymology point, a joke, a cultural reference). It is a guide so the reader knows the context before reading the English — not a translation of the scene. If a scene is a sponsor/self-promotion segment, say so ("这一段是推广").
- Use full-width Chinese punctuation (，。：“”) in titles and summaries.

## 2. annotations.json

```json
{
  "annotations": [
    {"i": 6,  "span": "clean up my room", "zh": "收拾房间", "type": "phrase", "note": "clean up 侧重收拾整齐；可拆开说 clean it up"},
    {"i": 10, "span": "duvet", "zh": "羽绒被、被子", "type": "word", "note": "法语借词，结尾 t 不发音；美式常说 comforter"},
    {"i": 209, "span": "Am I cooked?", "zh": "我是不是完蛋了", "type": "slang", "note": "网络流行语，cooked = 完了、没救了"},
    {"i": 137, "span": "break and fast", "zh": "break 打破 + fast 禁食", "type": "culture", "note": "breakfast 即打破一夜的禁食"}
  ],
  "corrections": [
    {"i": 197, "span": "bulldog sauce", "fix": "Buldak sauce", "note": "韩国火鸡面品牌 Buldak（불닭），字幕误识别为 bulldog"}
  ]
}
```

(`annotations.json` may also be a list of such objects — one per chunk — when the work was split.)

### What to highlight
- **phrase** — natural collocations and sentence patterns a learner can reuse: "when you think about it", "I'm not even gonna lie", "working with what we have", "leave for + 地点".
- **word** — everyday vocabulary an intermediate learner may not know: duvet, hamper, chug, drain, skyline.
- **slang** — informal / internet usage: "Am I cooked?", "Come on bro", "a little extra".
- **culture** — etymology, superstition, brands, food, platform conventions: apartment (from Italian), POV, "click the link in the description", Buldak.

Skip what a beginner already knows (bed, water, laptop, red). Prefer the meaningful chunk over the bare word ("clean up my room", not "clean"). Target about 0.4–0.7 highlights per sentence overall (≈ 1 every 2 sentences); denser pages become hard to read. A sentence gets at most 2 highlights.

When a first pass comes out denser than that, cut in this order: items a beginner already knows (though, as well, brush my teeth); repeats of a pattern already taught earlier; items whose only value is a note restating the sentence. Keep less obvious reusable chunks (a number of, just about, come along) ahead of words the video itself explains.

The type follows the item — there is no quota. Lesson-style videos are naturally phrase-heavy; vlogs have more slang and culture.

### Field rules (build.py and check.py depend on these)
- `span` must be copied **exactly** from sentence `i` (case, apostrophes, punctuation) — the page finds it by plain text search. 1–7 words; leave out trailing punctuation unless it belongs to the expression ("Am I cooked?").
- Spans in the same sentence must not overlap. Annotate an expression once, at its first natural occurrence — later duplicates are skipped.
- `zh`: the Chinese meaning **in this context**, ≤ 16 characters. Not a dictionary list. Check it against what the video actually shows: a staffroom where teachers chat and eat lunch is 教师休息室, not 办公室; deodorant is 除臭剂/香体露, not 止汗剂 (that's antiperspirant). A near-equivalent that names a different thing is a wrong gloss, and the learner will remember it.
- `note`: optional, ≤ 45 characters, or `""`. Useful kinds: register (口语/正式), US vs UK usage, a grammar point (practice + -ing; stuff 不可数), a common mistake, a pronunciation contrast (tear /ter/ 撕 vs /tɪr/ 流泪). Don't pad, and don't put IPA for the span itself here — that goes in ipa.json.
- `say` (optional): what text-to-speech should read when the span would be mispronounced, e.g. `"say": "N.P.C."`. 2–3-letter all-caps acronyms (POV, AC, DIY) are already spelled out automatically.
- Never write a Chinese translation of a whole sentence anywhere. The Chinese layer is scene guides + phrase glosses only (see SKILL.md for why).

### Corrections
Use corrections for real caption mistakes that would confuse a learner: misrecognized words or brand names (bulldog → Buldak), a name or dish the captions mangled, missing sentence breaks that run two sentences together ("duvet This here" → ". This here"), "1.38 pm" → "1:38 p.m.". Only list ones you are confident about; when guessing (e.g. a dish name), say it is a guess in the note.

- `span` must be exact and must **not overlap** a highlight in the same sentence. If the error touches a highlighted word, narrow the span — e.g. highlight `duvet`, and correct `" This here"` → `". This here"` (the leading space is part of the span).
- For unpunctuated auto captions, don't "fix" punctuation — it is missing everywhere; only fix misrecognized words.

## 3. ipa.json

Run `check.py <work> --ipa-todo` after annotations are final; it writes `ipa_todo.json` with every single word and ≤ 2-word item (plus context). Write one entry for each:

```json
[{"span": "duvet", "ipa": "/duːˈveɪ/"}, {"span": "tear open", "ipa": "/ˌter ˈoʊpən/"}]
```

Conventions — keep them identical across items so the page reads consistently:
- General American, Cambridge-Dictionary-US style, between slashes, no syllable dots, no flap diacritic (write t, not t̬).
- Vowels: iː ɪ e æ ɑː ɔː ʊ uː ʌ ə ɚ ɝː eɪ aɪ ɔɪ oʊ aʊ ɪr er ʊr ɑːr ɔːr; consonants θ ð ʃ ʒ tʃ dʒ ŋ j. No British /ɒ/ or /əʊ/.
- ˈ primary and ˌ secondary stress before the stressed syllable.
- Transcribe the span as written (plural /z/ vs /s/, past /d/ vs /t/) and in the sense used in the sentence (tear = rip → /ter/; tear up = cry → /ˌtɪr ˈʌp/; progress noun → /ˈprɑːɡres/).
- Multi-word items: words separated by spaces, and every stressed word gets a mark, monosyllables included.
  - Phrasal verbs stress the particle: wake up /ˌweɪk ˈʌp/, go off /ˌɡoʊ ˈɑːf/, tear up /ˌtɪr ˈʌp/.
  - Noun compounds stress the first part, secondary on the second: snooze button /ˈsnuːz ˌbʌtən/, traffic jams /ˈtræfɪk ˌdʒæmz/, garbage can /ˈɡɑːrbɪdʒ ˌkæn/.
  - Adjective + noun stresses both: dirty dishes /ˈdɝːti ˈdɪʃɪz/.
  - Function words take their weak form: as well /əz ˈwel/, to /tə/ before a consonant.
  - Letters: POV → /ˌpiːoʊˈviː/. When Cambridge US lists two pronunciations, use the first (off /ɑːf/).
- Length limits in this guide count every character — Chinese characters, Latin letters, spaces and punctuation each count as 1, exactly as check.py counts them.

IPA is easy to get subtly wrong. Re-read the whole list once specifically hunting for British vowels, wrong stress, and wrong endings — or have an independent checker do it (section 4).

## 4. Splitting the work for long videos

Up to ~120 sentences: do everything yourself in order. Beyond that, split annotation by scene groups of roughly 50–90 sentences. If the Agent tool is available, run one annotator per group and then one independent checker per group (the checker re-reads the sentences, fixes wrong spans/glosses, drops trivial or duplicate items, adds clearly missed ones, and keeps only certain corrections). Give each agent: the path to `sents.tsv`, the sentence-number range, this file's path (sections 2–3), and the target count for its range. Save each group's result and combine them into one `annotations.json` (a list of the group objects is fine). For IPA, one transcriber plus two independent checkers, then decide the disputed items yourself.

Whatever the split, run `check.py` on the combined result and fix every ERROR before building.
