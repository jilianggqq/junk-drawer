# junk-drawer

A personal collection of **Codex & Claude Code skills** for working with English–Chinese subtitles.

[Skills](#skills) · [Getting started](#getting-started)

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
