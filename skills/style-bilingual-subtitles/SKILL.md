---
name: style-bilingual-subtitles
description: Apply a user-selected saved bilingual subtitle style to a subtitle file or all subtitle files in a folder. Use for subtitle appearance, including fonts, colors, sizes, and positioning, rather than timing synchronization.
---

# Style Bilingual Subtitles

If the invocation does not already include a target, ask the user to enter a folder path or subtitle filename. Resolve a relative name against the working directory; ask which file if it is ambiguous. Ask which saved style to apply on every invocation unless the user explicitly selected one in that invocation. List the current choices with `python3 <skill-directory>/scripts/apply_style.py --list-styles`; use the registry rather than a hardcoded menu. If both target and style are missing, ask for them together. Wait for the selection before modifying files. Do not ask for a reference subtitle when applying a saved preset.

For a folder, process subtitle files recursively, excluding symlinks and directories named sub_backup, backup, backups, .git, or .codex. Inventory supported and unsupported formats, and report any skipped files. The helper supports ASS and SRT. For other text subtitle formats, convert to ASS with an available format-aware tool while preserving originals and verifying cue text and times. Bitmap subtitles require OCR and are outside this styling operation; report them rather than silently skipping or attempting OCR.

Run the bundled helper with the resolved path:

```sh
python3 <skill-directory>/scripts/apply_style.py '<target-path>' --style '<preset-id>'
```

Before writing any styled subtitle, the helper copies its original bytes and file metadata to `sub_backup/<original-filename>.bak` beside the source subtitle, creating `sub_backup/` if needed or reusing the existing directory. This applies to both ASS and SRT inputs. It then replaces ASS files in place and creates `.ass` siblings for SRT inputs, retaining the source SRT as well. For recursive folder processing, each source directory gets its own `sub_backup/`; never process files inside these backup directories. Existing backups or output files are never overwritten; investigate and report a collision rather than deleting them. It prepares and validates the whole supported batch before writing. A runtime write failure can leave a partial batch: inspect and report that state before retrying.

Presets live in `assets/styles/presets.json`, with self-contained ASS templates beside it. Saved choices include amber English above white Chinese, pale gold Chinese above English, and white Chinese above white English (with different language fonts). Templates capture full style definitions and script resolution. The pale gold preset captures the reference's normal bilingual dialogue appearance, including its English size override; scene-specific titles, annotations, drawings, and credits are not applied to ordinary dialogue. Rendering requires the named fonts or installed font fallbacks; do not silently substitute different font choices.

The helper splits bilingual lines and groups matching start/end timestamps. The selected preset either emits separate positioned language events or one combined event in the specified language order, preserving timings and visible text. Source appearance overrides are intentionally removed to enforce the saved style. Language is inferred from explicit English/Chinese style names or line-level Han/Latin content. Ambiguous mixed-language lines, drawings, and animated effects are rejected for inspection rather than guessed. Inspect rejected files and ask only for decisions that cannot be inferred from their content. Never translate, retime, or rename video files.

After processing, report changed files, preserved originals, outputs, and any skipped or failed files. Confirm timing and visible text preservation (SRT milliseconds round to the nearest ASS centisecond, up to 5 ms); cue count may grow when bilingual cues become two language events.

## Adding another style

When asked to add a style, inspect the supplied reference's script resolution, style definitions, and dialogue overrides. Identify normal dialogue separately from titles, signs, and effects. Capture the actual language order, fonts, font sizes, colors, outlines, shadows, alignment, and margins. Do not assume every preset places English first.

Add a descriptive stable preset ID and a standalone ASS template under `assets/styles/`. Exclude reference filenames, media paths, project metadata, and dialogue text from saved assets. Add its label, visual description, template filename, language order, and layout to `presets.json`. Existing presets must remain available. No original reference file is needed after capture.

For `separate` layout, the template needs styles named `English` and `Chinese`; supply `positions` for both languages. For `combined` layout, supply the template's dialogue `style` name and per-language `font_sizes`. Optional `font_names` supplies per-language font overrides; when omitted, both languages inherit the template font. Preserve omitted script resolution when the reference relies on ASS defaults. All other visual fields come from the template. If a future style needs another layout mechanic, extend the helper and test that behavior rather than approximating it silently. The menu reads the registry automatically, so adding supported presets requires no processing-code changes.

Test each added preset using temporary English-only, Chinese-only, bilingual, and separate-event samples. Verify visible text and timing preservation, order, full style values, backup protection, and compatibility with existing presets. Do not restyle user subtitles merely to test a skill update.

## Sync after AI edits

Whenever an AI modifies this skill, automatically synchronize the complete skill folder between `/Users/qiqiangguan/.codex/skills/style-bilingual-subtitles` and `/Users/qiqiangguan/GQQ/GitLocal/junk-drawer/skills/style-bilingual-subtitles` before reporting completion. This applies to `SKILL.md`, scripts, assets, presets, and other maintained skill files. Apply the final changes to both copies, including intentional file additions, renames, and removals; exclude generated caches such as `__pycache__` and `.pyc` files. Inspect differences first and preserve unrelated edits rather than blindly overwriting them. Verify that the maintained files match after syncing. If synchronization fails, report the failure and remaining differences explicitly. This requirement authorizes local synchronization; commit or push only when the user requests it.
