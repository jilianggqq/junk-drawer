#!/usr/bin/env python3
"""Merge a <base>.en.srt + <base>.cs.srt (or .ct.srt) pair into a bilingual
<base>.en_cs.ass file: English above, Chinese below, English colored
&H0062A8EB to match ~/.claude/commands/subtitle-color.md.

Each cue's English text is joined into a single line, and each cue's
Chinese text is joined into a single line (multi-line SRT cues are
collapsed with spaces rather than kept as separate ASS lines).

English/Chinese cues that overlap in time (i.e. represent the same line of
dialogue, translated separately with slightly different in/out points) are
snapped to a shared [min(start), max(end)] window, so both languages appear
and disappear together instead of one showing before the other. Each line
also carries an explicit \\pos() override so its screen position is fixed
(English just above Chinese, both above the bottom edge) rather than left
to the player's automatic collision-avoidance, which can otherwise flip
Chinese above English when two simultaneous lines are considered to
"collide".

After writing the .ass file, the source .en.srt and .cs.srt/.ct.srt files
are moved into an "assembly" subfolder next to them, for backup.

Usage:
    merge_to_ass.py <base_path>

<base_path> may include a directory, e.g. /movies/Show.S02E03
Looks for <base_path>.en.srt and <base_path>.cs.srt (falling back to .ct.srt).
Writes <base_path>.en_cs.ass
"""
import re
import sys
from pathlib import Path

ENGLISH_COLOR = "&H0062A8EB"  # matches /subtitle-color.md
CHINESE_COLOR = "&H00FFFFFF"

# PlayResY - MarginV for each style (bottom-aligned anchor y), used both by
# the Style MarginV values below and by the explicit \pos() override so the
# stacking order (English above Chinese) is deterministic instead of being
# subject to the renderer's automatic collision-avoidance.
PLAY_RES_X = 1920
PLAY_RES_Y = 1080
ENGLISH_MARGIN_V = 90
CHINESE_MARGIN_V = 30
ENGLISH_POS_Y = PLAY_RES_Y - ENGLISH_MARGIN_V
CHINESE_POS_Y = PLAY_RES_Y - CHINESE_MARGIN_V
POS_X = PLAY_RES_X // 2

HEADER = """[Script Info]
Title: {title}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: English,Arial,52,{en_color},&H000000FF,&H00000000,&H00808080,0,0,0,0,100,100,0,0,1,3,0,2,10,10,{en_margin_v},1
Style: Chinese,Microsoft YaHei,56,{cs_color},&H000000FF,&H00000000,&H00808080,0,0,0,0,100,100,0,0,1,3,0,2,10,10,{cs_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

SRT_BLOCK_RE = re.compile(
    r"\d+\s*\n"
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3}).*?\n"
    r"(.*?)(?=\n\s*\n\d+\s*\n|\Z)",
    re.DOTALL,
)


def srt_time_to_seconds(t: str) -> float:
    t = t.replace(",", ".")
    h, m, rest = t.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def seconds_to_ass(sec: float) -> str:
    cs_total = round(sec * 100)
    h, rem = divmod(cs_total, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def strip_tags(text: str) -> str:
    text = re.sub(r"</?font[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[bi]>", "", text, flags=re.IGNORECASE)
    # Some source SRTs carry leftover ASS override tags (e.g. "{\an8}" to
    # force top position) from being converted out of an .ass file. These
    # would hijack our own \pos()/alignment if left in, so strip any
    # "{\...}" block.
    text = re.sub(r"\{\\[^}]*\}", "", text)
    return text.strip()


def parse_srt(path: Path):
    content = path.read_text(encoding="utf-8-sig")
    cues = []
    for m in SRT_BLOCK_RE.finditer(content.strip() + "\n\n"):
        start, end, text = m.groups()
        text = strip_tags(text.strip())
        text = " ".join(line.strip() for line in text.splitlines() if line.strip())
        if text:
            cues.append((srt_time_to_seconds(start), srt_time_to_seconds(end), text))
    return cues


def pair_cues(en_cues, cs_cues):
    """Greedily walk both (time-sorted) cue lists, snapping overlapping
    English/Chinese cues to a shared [min(start), max(end)] window so the
    same line of dialogue shows and hides at the same time in both
    languages. Cues with no overlapping counterpart keep their own timing.

    Returns a list of (style, start_sec, end_sec, text) tuples.
    """
    events = []
    i = j = 0
    while i < len(en_cues) and j < len(cs_cues):
        e_start, e_end, e_text = en_cues[i]
        c_start, c_end, c_text = cs_cues[j]
        overlap = min(e_end, c_end) - max(e_start, c_start)
        if overlap > 0:
            start = min(e_start, c_start)
            end = max(e_end, c_end)
            events.append(("English", start, end, e_text))
            events.append(("Chinese", start, end, c_text))
            i += 1
            j += 1
        elif e_start <= c_start:
            events.append(("English", e_start, e_end, e_text))
            i += 1
        else:
            events.append(("Chinese", c_start, c_end, c_text))
            j += 1
    while i < len(en_cues):
        e_start, e_end, e_text = en_cues[i]
        events.append(("English", e_start, e_end, e_text))
        i += 1
    while j < len(cs_cues):
        c_start, c_end, c_text = cs_cues[j]
        events.append(("Chinese", c_start, c_end, c_text))
        j += 1
    return events


def main():
    if len(sys.argv) != 2:
        print("Usage: merge_to_ass.py <base_path>", file=sys.stderr)
        sys.exit(1)

    base = Path(sys.argv[1])
    en_path = base.with_name(base.name + ".en.srt")
    cs_path = base.with_name(base.name + ".cs.srt")
    if not cs_path.exists():
        ct_path = base.with_name(base.name + ".ct.srt")
        if ct_path.exists():
            cs_path = ct_path

    if not en_path.exists():
        print(f"Missing {en_path}", file=sys.stderr)
        sys.exit(1)
    if not cs_path.exists():
        print(f"Missing {cs_path} (also checked .ct.srt)", file=sys.stderr)
        sys.exit(1)

    en_cues = parse_srt(en_path)
    cs_cues = parse_srt(cs_path)
    events = pair_cues(en_cues, cs_cues)
    events.sort(key=lambda e: e[1])

    out_path = base.with_name(base.name + ".en_cs.ass")
    with out_path.open("w", encoding="utf-8") as f:
        f.write(HEADER.format(
            title=base.name,
            play_res_x=PLAY_RES_X,
            play_res_y=PLAY_RES_Y,
            en_color=ENGLISH_COLOR,
            cs_color=CHINESE_COLOR,
            en_margin_v=ENGLISH_MARGIN_V,
            cs_margin_v=CHINESE_MARGIN_V,
        ))
        for style, start, end, text in events:
            pos_y = ENGLISH_POS_Y if style == "English" else CHINESE_POS_Y
            pos_tag = f"{{\\pos({POS_X},{pos_y})}}"
            f.write(
                f"Dialogue: 0,{seconds_to_ass(start)},{seconds_to_ass(end)},"
                f"{style},,0,0,0,,{pos_tag}{text}\n"
            )

    print(f"Wrote {out_path} ({len(en_cues)} English + {len(cs_cues)} Chinese cues)")

    assembly_dir = base.parent / "assembly"
    assembly_dir.mkdir(exist_ok=True)
    for src in (en_path, cs_path):
        dest = assembly_dir / src.name
        src.rename(dest)
        print(f"Moved {src.name} -> {dest}")


if __name__ == "__main__":
    main()
