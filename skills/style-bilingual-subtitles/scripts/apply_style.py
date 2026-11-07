"""Apply the bundled bilingual style using only the Python standard library."""
import argparse
from pathlib import Path
import re
import shutil
import json

STYLE_DIR = Path(__file__).resolve().parent.parent / 'assets/styles'
PRESETS = json.loads((STYLE_DIR / 'presets.json').read_text(encoding='utf-8'))


def load_preset(name):
    preset = PRESETS[name]
    template = (STYLE_DIR / preset['template']).resolve()
    if template.parent != STYLE_DIR.resolve():
        raise ValueError('Template must be inside the style directory')
    if preset['layout'] not in ('separate', 'combined') or set(preset['order']) != {'English', 'Chinese'}:
        raise ValueError('Invalid preset layout/order')
    return preset, template.read_text(encoding='utf-8')
HAN = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
LATIN = re.compile(r'[A-Za-z]')
TAG = re.compile(r'\{[^}]*\}')
EXCLUDED = {'backup', 'backups', 'sub_backup', '.git', '.codex'}


def language(text, hint):
    if HAN.search(text) and LATIN.search(text):
        if hint.lower() in ('english', 'chinese'):
            return hint.title()
        raise ValueError('Mixed-language line needs inspection: ' + text[:100])
    if HAN.search(text):
        return 'Chinese'
    if LATIN.search(text):
        return 'English'
    if hint.lower() in ('english', 'chinese'):
        return hint.title()
    raise ValueError('Cannot determine language: ' + text[:100])


def decode(path):
    raw = path.read_bytes()
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    return raw.decode('utf-8-sig')


def ass_cues(text):
    section = ''
    fields = None
    cues = []
    for line in text.splitlines():
        if line.strip().startswith('['):
            section = line.strip().lower()
        if section != '[events]':
            continue
        if line.lower().startswith('format:'):
            fields = [x.strip().lower() for x in line.split(':', 1)[1].split(',')]
            if fields[-1] != 'text':
                raise ValueError('ASS Text field must be last')
        if line.lower().startswith('dialogue:'):
            if fields is None:
                raise ValueError('Missing Events Format')
            values = line.split(':', 1)[1].lstrip().split(',', len(fields)-1)
            if len(values) != len(fields):
                raise ValueError('Malformed dialogue')
            row = dict(zip(fields, values))
            if row.get('effect', '').strip() or re.search(r'\\(?:p[1-9]|t\s*\(|k[fo]?\d)', row['text'], re.I):
                raise ValueError('Drawing, animation, or karaoke needs inspection')
            cues.append((row['start'], row['end'], row['text'], row.get('style', '')))
    return cues


def ass_time(value):
    h, m, s, ms = map(int, re.split('[:,.]', value))
    # ASS resolution is centiseconds; round SRT milliseconds to nearest centisecond.
    ticks = (h*3600 + m*60 + s)*100 + (ms+5)//10
    return f'{ticks//360000}:{ticks//6000%60:02}:{ticks//100%60:02}.{ticks%100:02}'


def srt_cues(text):
    cues = []
    for block in re.split(r'\n\s*\n', text.replace('\r\n', '\n').strip()):
        lines = block.splitlines()
        if lines and lines[0].strip().isdigit():
            lines.pop(0)
        if not lines:
            continue
        match = re.fullmatch(r'\s*(\d+:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d+:\d{2}:\d{2}[,.]\d{3})\s*', lines[0])
        if not match:
            raise ValueError('Unsupported SRT cue header')
        content = re.sub(r'</?(?:i|b|u|font)\b[^>]*>', '', r'\N'.join(lines[1:]), flags=re.I)
        cues.append((ass_time(match[1]), ass_time(match[2]), content, ''))
    return cues


def transform(path, preset_name):
    preset, header = load_preset(preset_name)
    text = decode(path)
    cues = ass_cues(text) if path.suffix.lower() == '.ass' else srt_cues(text)
    if not cues:
        raise ValueError('No subtitle cues')
    events = []
    timeline = {}
    for start, end, content, hint in cues:
        grouped = timeline.setdefault((start, end), {'English': [], 'Chinese': []})
        for part in re.split(r'\\[Nn]|\n', TAG.sub('', content).replace(r'\h', ' ')):
            if part.strip():
                grouped[language(part, hint)].append(part)
    for (start, end), grouped in timeline.items():
        if preset['layout'] == 'separate':
            for style in preset['order']:
                parts = grouped[style]
                if not parts:
                    continue
                pos = preset['positions'][style]
                body = r'\N'.join(parts)
                events.append(f'Dialogue: 0,{start},{end},{style},,0,0,0,,{{\\pos({pos})}}{body}')
        else:
            lines = []
            for language_name in preset['order']:
                size = preset['font_sizes'][language_name]
                font = preset.get('font_names', {}).get(language_name)
                font_tag = f'\\fn{font}' if font else ''
                for part in grouped[language_name]:
                    lines.append(f'{{{font_tag}\\fs{size}}}' + part)
            if lines:
                body = r'\N'.join(lines)
                style = preset['style']
                events.append(f'Dialogue: 0,{start},{end},{style},,0,0,0,,{body}')
    if not events:
        raise ValueError('No visible subtitle text')
    result = header + '\n'.join(events) + '\n'
    # Reparse the generated document before allowing any write.
    assert len(ass_cues(result)) == len(events)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path, nargs='?')
    parser.add_argument('--style', choices=sorted(PRESETS))
    parser.add_argument('--list-styles', action='store_true')
    args = parser.parse_args()
    if args.list_styles:
        for name, preset in PRESETS.items():
            print(f"{name}: {preset['label']} — {preset['description']}")
        return
    if args.target is None or args.style is None:
        parser.error('Supply a target and --style; use --list-styles to see choices')
    load_preset(args.style)
    target = args.target.expanduser().absolute()
    if target.is_symlink() or not target.exists():
        parser.error('Target must exist and not be a symlink')
    files = [target] if target.is_file() else sorted(p for p in target.rglob('*') if p.is_file() and not p.is_symlink() and not any(x.lower() in EXCLUDED for x in p.relative_to(target).parts[:-1]) and not any((target / Path(*p.relative_to(target).parts[:i])).is_symlink() for i in range(1, len(p.relative_to(target).parts))))
    plans = []
    destinations = set()
    for path in files:
        ext = path.suffix.lower()
        if ext not in ('.ass', '.srt'):
            if ext in ('.ssa', '.vtt', '.sub', '.idx', '.sup', '.smi', '.ttml') or target.is_file():
                print(f'SKIPPED unsupported: {path}')
            continue
        output = path if ext == '.ass' else path.with_suffix('.ass')
        backup_dir = path.parent / 'sub_backup'
        if backup_dir.is_symlink() or (backup_dir.exists() and not backup_dir.is_dir()):
            raise ValueError(f'Backup folder must be a real directory: {backup_dir}')
        backup = backup_dir / (path.name + '.bak')
        if output in destinations or (output != path and output.exists()) or (backup and backup.exists()):
            raise ValueError(f'Output/backup collision: {path}')
        destinations.add(output)
        plans.append((path, output, backup, transform(path, args.style)))
    for path, output, backup, content in plans:
        if backup:
            backup.parent.mkdir(exist_ok=True)
            # Exclusive creation prevents overwriting a backup.
            with backup.open('xb') as stream:
                stream.write(path.read_bytes())
            shutil.copystat(path, backup)
        if output == path:
            output.write_text(content, encoding='utf-8-sig')
        else:
            with output.open('x', encoding='utf-8-sig') as stream:
                stream.write(content)
        assert output.read_text(encoding='utf-8-sig') == content
        print(f'STYLED {output}' + (f' (original: {backup})' if backup else f' (original retained: {path})'))
    print(f'Completed {len(plans)} subtitle files. SRT times rounded to ASS centiseconds.')


if __name__ == '__main__':
    main()
