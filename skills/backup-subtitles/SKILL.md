---
name: backup-subtitles
description: Back up subtitle files recursively from a folder into the local junk-drawer subtitles archive, organized by show and season, without changing source files.
---

# Backup Subtitles

Accept a folder path; ask for it only if missing. Ask which folders the user wants excluded unless the current request already specifies exclusions or explicitly requests none. Wait for that answer before copying; an explicit “none” includes all folders. Exclusions apply only to the current request. Never persist user-specific exclusion lists in this skill or its script. Copy subtitle sidecars, not video files or embedded tracks. Default destination: `~/GQQ/GitLocal/junk-drawer/subtitles`.

Run the bundled helper first with `--dry-run` to inspect mappings and collisions, then without it to copy:

```sh
python3 <skill-directory>/scripts/backup_subtitles.py '<source-folder>' --dry-run
python3 <skill-directory>/scripts/backup_subtitles.py '<source-folder>'
```

The helper supports ASS, SRT, SSA, VTT, SUB, IDX, SUP, SMI, TTML, and SBV. There are no built-in folder exclusions. Symlinks are skipped. Pass user-selected exclusions with repeatable `--exclude` options in both preview and copy commands. A single folder name excludes matching directories anywhere below the source; a path with multiple components excludes that folder relative to the source. Matching is case-sensitive. Exclusions must be relative paths without `..`. To skip the entire selected source, do not run the copy.

```sh
python3 <skill-directory>/scripts/backup_subtitles.py '<source-folder>' --exclude '<folder-name>' --exclude '<relative/folder-path>' --dry-run
```

Remove `--dry-run` after inspecting the plan. With no `--exclude` options, all folders are included. If included files map to the same destination, report the collision and ask for a mapping or exclusion decision; do not silently discard either file.

Preserve subtitle filenames under `{show}/Season{number}/`. Infer show and season from the TVShows hierarchy, season folders (`Season1`, `S01`), season suffixes (`ExampleShowS3` becomes `ExampleShow/Season3`), or `SxxExx` filenames. A selected season still belongs under its parent show. Inspect dry-run mappings; if an unfamiliar hierarchy cannot be inferred reliably, ask for the missing show/season mapping rather than guessing.

Identical existing backups are skipped. Different existing backups are preserved; new content is copied with a `.backup-<timestamp>` suffix before its extension. Multiple inputs mapping to the same destination cause a preflight error before any copying. Never delete or overwrite archived files. The helper copies bytes and metadata and verifies SHA-256 for each new copy. On a runtime failure, inspect partial results before retrying. Do not commit or push unless requested.

Report the destination, copied and unchanged counts, exclusions, mapping ambiguities, and failures. Source files must remain unchanged.

## Sync after AI edits

Whenever this skill is modified, inspect and synchronize maintained files between `~/.codex/skills/backup-subtitles` and `~/GQQ/GitLocal/junk-drawer/skills/backup-subtitles`. Preserve unrelated edits; exclude `__pycache__` and `.pyc`. Verify both maintained copies match before reporting completion. Local synchronization is authorized; commit or push only on request.
