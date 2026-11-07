---
name: bilingual-subtitles
description: Extract English and Chinese text subtitles from video files with ffprobe and ffmpeg, then merge SRT pairs into styled bilingual ASS subtitles with amber English above white Chinese. Use for English-Chinese subtitle extraction, merging, or styling.
---

Paths below are relative to the current working directory unless the user
gives absolute paths. `<script-dir>` is the `scripts/` folder beside this SKILL.md. Resolve it from
the installed skill location. Requires Python 3, ffprobe, and ffmpeg. The
merge script uses only Python’s standard library.

## Workflow

### 1. Get video file(s)
If the user didn't already give video file path(s) or a folder, ask for
them. Accept:
- One or more explicit filenames (`The.Big.Bang.Theory.S02E03.mkv`)
- A range shorthand like `The.Big.Bang.Theory.S02E03-24.mkv` — expand this
  to the individual episode files that actually exist in that directory
  (e.g. S02E03.mkv … S02E24.mkv) before processing; don't guess files that
  aren't on disk.
- A folder — discover video files in it (`.mkv .mp4 .avi .mov .wmv .flv .ts
  .m2ts .webm`).

### 2. Extract subtitles
For each video, base = filename without extension.

Analyze streams:
```
ffprobe -v quiet -print_format json -show_streams -select_streams s "<video_path>"
```
Identify subtitle streams by `tags.language` (`chi`/`zho`/`chs`/`cht`/`eng`)
and `tags.title` keywords (Simplified/Traditional/CHS/CHT/SC/TC/English).
Skip image-based codecs (`hdmv_pgs_subtitle`, `dvd_subtitle`) — note they
can't be extracted to SRT.

Chinese (prefer Simplified, fall back to Traditional):
```
ffmpeg -i "<video_path>" -map 0:<stream_index> -c:s srt "<base>.cs.srt"
```
If only Traditional exists, still name it `<base>.cs.srt` for this
skill's purposes (the merge script also accepts `.ct.srt` if that's what
exists — see step 3).

English (prefer the track without SDH/Forced qualifiers if multiple):
```
ffmpeg -i "<video_path>" -map 0:<stream_index> -c:s srt "<base>.en.srt"
```

If a language is missing, report it and skip that half of the merge step
for that video (you need both `.en.srt` and a Chinese `.srt` to merge).

Reuse existing matching SRTs when available. Check output and `assembly/`
paths for collisions before extraction or merging; do not silently
overwrite existing subtitles or backups. If embedded text subtitles are
unavailable, report this instead of inventing translations or running OCR.

### 3. Merge into bilingual ASS
```
python3 <script-dir>/merge_to_ass.py "<dir>/<base>"
```
Reads `<base>.en.srt` and `<base>.cs.srt` (or `<base>.ct.srt` as fallback),
writes `<base>.en_cs.ass` — English styled above Chinese, English
`PrimaryColour` set to `&H0062A8EB` (`#EBA862`), Chinese left white. The script sets the color directly in the
`[V4+ Styles]` section it writes.

Each cue's text is collapsed to a single line: if the source SRT cue had
multiple lines, they're joined with a space (English stays one English
line, Chinese stays one Chinese line — never a `\N` break within a cue).

English/Chinese cues that overlap in time (the usual case — they're the
same line of dialogue, translated separately with slightly different
in/out points) are snapped to a shared `[min(start), max(end)]` window, so
both languages appear and disappear together instead of one preceding the
other. Cues with no overlapping counterpart keep their own timing. Each
line also gets an explicit `\pos()` override (English above, Chinese at
the very bottom) so the stacking order is fixed instead of depending on
the player's automatic collision-avoidance, which otherwise can flip
Chinese above English when two simultaneous lines are considered to
overlap on screen.

After writing the `.en_cs.ass`, the script moves the source `<base>.en.srt`
and `<base>.cs.srt`/`.ct.srt` into an `assembly/` subfolder next to them
(created if missing), for backup. Don't re-extract or re-move manually —
the script does this automatically per video, so it's already reflected
after step 3 runs for that video.

### 4. Report
For each video: streams found, which Chinese variant was used, files
created (`.en_cs.ass`) and where the source `.en.srt`/`.cs.srt`/`.ct.srt`
were moved (`<dir>/assembly/`), and any warnings (missing language,
image-based subs skipped).

## Gotchas
- `merge_to_ass.py` strips `<font>`/`<b>`/`<i>` tags from the SRT text
  before writing Dialogue lines — ASS styling is done via the Style
  section, not inline tags.
- SRT timestamps use `,` for milliseconds; ASS uses `.` with centiseconds
  — the script converts this (`00:00:01,000` → `0:00:01.00`).
- The script greedily pairs overlapping English/Chinese cues one-to-one
  and shares their timing window. Unpaired cues keep their original timing.
  Events are sorted and same-language overlaps are trimmed to prevent
  fixed-position lines from rendering on top of each other.
- Multi-line SRT cues are joined into one line per language (space-joined),
  not kept as multiple ASS lines.
- Overlapping English/Chinese cue pairs are re-timed to a shared window and
  every line carries a `\pos()` override — both fixes require the sources
  to still be time-sorted (as SRT cues normally are); don't hand-edit the
  `.en.srt`/`.cs.srt` into out-of-order cues before merging.
- Some source SRTs (seen on Chinese tracks converted out of an original
  `.ass`) carry leftover inline override tags like `{\an8}` (forces top
  alignment) on individual cues. `strip_tags()` strips any `{\...}` block
  for exactly this reason — without it, those cues would render at the top
  of the screen instead of the bottom, which was the direct cause of
  "Chinese sometimes appears at the top" before this was added.
- The script moves (not copies) `.en.srt`/`.cs.srt`/`.ct.srt` into
  `assembly/` after a successful merge — if you need to re-run the merge
  for a video, the sources will be in `assembly/`, not next to the video.

## Sync after AI edits

Whenever an AI modifies this skill, automatically synchronize the complete skill folder between `/Users/qiqiangguan/.codex/skills/bilingual-subtitles` and `/Users/qiqiangguan/GQQ/GitLocal/junk-drawer/skills/bilingual-subtitles` before reporting completion. This applies to `SKILL.md`, scripts, assets, presets, and other maintained skill files. Apply the final changes to both copies, including intentional file additions, renames, and removals; exclude generated caches such as `__pycache__` and `.pyc` files. Inspect differences first and preserve unrelated edits rather than blindly overwriting them. Verify that the maintained files match after syncing. If synchronization fails, report the failure and remaining differences explicitly. This requirement authorizes local synchronization; commit or push only when the user requests it.
