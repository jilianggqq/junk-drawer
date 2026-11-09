# junk-drawer

A personal collection of **Codex & Claude Code skills** and **English–Chinese subtitle backups**.

[Skills](#skills) · [Getting started](#getting-started) · [Subtitle archive](#subtitle-archive)

## Skills

| Skill | What it does |
| --- | --- |
| [Bilingual subtitles](skills/bilingual-subtitles/SKILL.md) | Extract English and Chinese text subtitles from videos and merge them into styled ASS files. |
| [Style bilingual subtitles](skills/style-bilingual-subtitles/SKILL.md) | Apply saved subtitle styles while preserving text and timing, with originals saved in `sub_backup/`. |
| [Back up subtitles](skills/backup-subtitles/SKILL.md) | Archive subtitle files by show and season, preserve existing backups, and verify copied files. |

Available styles include amber English above white Chinese, pale gold Chinese above English, and white Chinese above white English.

## Getting started

1. Copy the desired folders from [`skills/`](skills/) into your assistant’s skills directory:

   | Assistant | Skills directory |
   | --- | --- |
   | Codex | `~/.codex/skills/` |
   | Claude Code | `~/.claude/skills/` |

2. Start a new session and ask your assistant to use the installed skill. For example, in Codex:

   ```text
   $bilingual-subtitles /path/to/season
   $style-bilingual-subtitles /path/to/season
   $backup-subtitles /path/to/TVShows
   ```

**Requirements:** Python 3 for the bundled scripts; `ffmpeg` and `ffprobe` for extracting subtitles from video. See each skill’s instructions for its workflow and options.

## Subtitle archive

Browse [`subtitles/`](subtitles/) by show and season:

| Show | 中文名 | Seasons |
| --- | --- | --- |
| [A Knight of Seven Kingdoms](subtitles/A%20Knight%20of%20Seven%20Kingdoms/) | 七王国的骑士 | 1 |
| [Clarkson’s Farm](subtitles/ClarksonFarm/) | 克拉克森的农场 | 3–5 |
| [Friends](subtitles/Friends/) | 老友记 | 1–10 |
| [Grey’s Anatomy](subtitles/GreysAnatomy/) | 实习医生格蕾 | 1 |
| [The Queen’s Gambit](subtitles/The%20Queens%20Gambit%20HD/) | 后翼弃兵/女王的棋局 | 1 |
| [The Last of Us](subtitles/The%20last%20of%20us/) | 最后生还者 | 1 |
| [The Big Bang Theory](subtitles/TheBigBangTheory/) | 生活大爆炸 | 1–2 |
| [True Detective](subtitles/True%20Detective/) | 真探 | 1 |
