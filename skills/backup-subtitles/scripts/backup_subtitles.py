"""Copy subtitle sidecars into a show/season archive without replacing backups."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
from datetime import datetime

EXTENSIONS = {'.ass', '.srt', '.ssa', '.vtt', '.sub', '.idx', '.sup', '.smi', '.ttml', '.sbv'}

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').digest()

def season_number(name):
    match = re.fullmatch(r'(?:Season\s*|S)(\d+)', name, re.I)
    return int(match[1]) if match else None

def location(path, source):
    # Prefer a TVShows ancestor, including when the selected source is one season.
    ancestors = list(path.parents)
    library = next((p for p in ancestors if p.name.lower() == 'tvshows'), None)
    if library:
        parts = path.relative_to(library).parts
        show = parts[0]
        directories = parts[1:-1]
    else:
        numbered = next((p for p in ancestors if season_number(p.name) is not None), None)
        if numbered:
            show = numbered.parent.name
            directories = [numbered.name]
        else:
            relative = path.relative_to(source)
            # A child containing season folders is a show under a collection root.
            if len(relative.parts) >= 3 and season_number(relative.parts[1]) is not None:
                show = relative.parts[0]
                directories = relative.parts[1:-1]
            else:
                show = source.name
                directories = relative.parts[:-1]
    season = next((season_number(p) for p in directories if season_number(p) is not None), None)
    attached = re.fullmatch(r'(.+?)S(\d+)', show, re.I)
    if attached:
        show = attached[1]
        season = season if season is not None else int(attached[2])
    episode = re.search(r'S(\d{1,2})E\d+', path.name, re.I)
    if season is None and episode:
        season = int(episode[1])
    if season is None:
        raise ValueError(f'Cannot infer season for {path}; ask the user for its show/season mapping')
    return show, season

def is_excluded(relative, exclusions):
    for value in exclusions:
        value = value.rstrip('/')
        rule = Path(value)
        if not value or rule.is_absolute() or '..' in rule.parts:
            raise ValueError('Exclusions must be folder names or paths relative to the source')
        if len(rule.parts) == 1:
            if value in relative.parts[:-1]:
                return True
        elif relative.parts[:len(rule.parts)] == rule.parts:
            return True
    return False

def backup(source, destination, dry_run=False, exclusions=()):
    source = source.expanduser().resolve(strict=True)
    destination = destination.expanduser().resolve()
    if not source.is_dir():
        raise ValueError('Source must be a directory')
    if destination == source or destination.is_relative_to(source):
        raise ValueError('Destination must be outside the source folder')
    # Validate rules even when there are no subtitles.
    is_excluded(Path('validation.ass'), exclusions)
    plans = []
    seen = set()
    unchanged = 0
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        relative = path.relative_to(source)
        if any(p.is_symlink() for p in [path, *path.parents]):
            continue
        if is_excluded(relative, exclusions):
            continue
        show, season = location(path, source)
        target = destination / show / f'Season{season}' / path.name
        if target in seen:
            raise ValueError(f'Multiple source files map to {target}; resolve before copying')
        seen.add(target)
        if any(p.is_symlink() for p in [target, *target.parents]):
            raise ValueError(f'Symlink in destination path: {target}')
        if target.exists():
            if digest(path) == digest(target):
                unchanged += 1
                continue
            # Preserve old backup under its original name; retain the new revision too.
            target = target.with_name(f'{target.stem}.backup-{stamp}{target.suffix}')
            if target.exists():
                raise ValueError(f'Revision collision: {target}')
        plans.append((path, target))
    for path, target in plans:
        if dry_run:
            print(f'COPY {path} -> {target}')
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with path.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        shutil.copystat(path, target)
        if digest(path) != digest(target):
            raise OSError(f'Backup verification failed: {target}')
    print(f'{"Planned" if dry_run else "Copied and verified"}: {len(plans)}; identical backups skipped: {unchanged}')
    return len(plans), unchanged

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--destination', type=Path, default=Path('~/GQQ/GitLocal/junk-drawer/subtitles'))
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--exclude', action='append', default=[], metavar='FOLDER',
                        help='Exclude a folder name anywhere or a source-relative folder path; repeatable')
    args = parser.parse_args()
    backup(args.source, args.destination, args.dry_run, args.exclude)

if __name__ == '__main__':
    main()
