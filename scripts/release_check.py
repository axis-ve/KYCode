"""Check the explicit public file set and optionally copy it into a fresh directory."""
import argparse
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zlib
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'personal or machine path': re.compile(r'/(?:Users|home|private/(?:tmp|var))/|[A-Z]:[\\/]Users[\\/]'),
    'credential-shaped value': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{30,}'),
    'email address': re.compile(r'[\w.+-]+@(?!users\.noreply\.github\.com)[\w.-]+\.[A-Za-z]{2,}'),
}
NOREPLY = '@users.noreply.github.com'
GITHUB_MERGE_COMMITTER = 'noreply' + '@' + 'github.com'


def findings(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        check_png(data)
        return []
    text = data.decode('utf-8')
    return [(number, kind) for number, line in enumerate(text.splitlines(), 1)
            for kind, pattern in RULES.items() if pattern.search(line)]


def check_png(data):
    """Allow image data and fixed-format color fields, but no embedded metadata."""
    offset = 8
    kinds = []
    fixed_sizes = {b'IHDR': 13, b'sRGB': 1, b'gAMA': 4, b'cHRM': 32, b'IEND': 0}
    while offset + 12 <= len(data):
        size = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(data):
            raise ValueError('Truncated PNG chunk')
        if kind != b'IDAT' and (kind not in fixed_sizes or size != fixed_sizes[kind]):
            raise ValueError('PNG contains unsupported chunks or metadata')
        checksum = struct.unpack('>I', data[end - 4:end])[0]
        if zlib.crc32(data[offset + 4:end - 4]) != checksum:
            raise ValueError('Invalid PNG checksum')
        kinds.append(kind)
        offset = end
        if kind == b'IEND':
            break
    if (offset != len(data) or not kinds or kinds[0] != b'IHDR'
            or kinds[-1] != b'IEND' or b'IDAT' not in kinds
            or kinds.count(b'IHDR') != 1):
        raise ValueError('Invalid PNG structure or trailing data')


def public_files(root):
    paths = (root / 'release-files.txt').read_text().splitlines()
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate release file')
    for name in paths:
        path = Path(name)
        if not name or path.is_absolute() or '..' in path.parts or '.git' in path.parts or findings(name.encode()):
            raise ValueError(f'Invalid release path: {name}')
        source = root / path
        if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Release path escapes the source: {name}')
        if not source.is_file():
            raise ValueError(f'Missing release file: {name}')
    return paths


def check(root):
    paths = public_files(root)
    problems = []
    for name in paths:
        for line, kind in findings((root / name).read_bytes()):
            problems.append(f'{name}:{line}: {kind}')
    if problems:
        raise ValueError('\n'.join(problems))
    return paths


def check_archive(path):
    expected = {Path(name).relative_to('skills').as_posix(): (ROOT / name).read_bytes()
                for name in public_files(ROOT) if name.startswith('skills/')}
    expected['INSTALL.txt'] = (ROOT / 'INSTALL.txt').read_bytes()
    with ZipFile(path) as archive:
        names = archive.namelist()
        if set(names) != set(expected) or len(names) != len(expected):
            raise ValueError('Archive members differ from the installable package')
        for name in archive.namelist():
            member = Path(name)
            if member.is_absolute() or '..' in member.parts:
                raise ValueError('Unsafe archive member')
            data = archive.read(name)
            if data != expected[name]:
                raise ValueError(f'Archive bytes differ from the source: {name}')
            hits = findings(data)
            if hits:
                raise ValueError(f'{name}: {hits}')


def identity_allowed(author, committer):
    """Authors must use a GitHub noreply address; GitHub commits pull request merges as itself."""
    return author.endswith(NOREPLY) and (committer.endswith(NOREPLY) or committer == GITHUB_MERGE_COMMITTER)


def check_index(root, paths):
    tracked = subprocess.check_output(['git', '-C', str(root), 'ls-files'], text=True).splitlines()
    if set(tracked) != set(paths):
        raise ValueError('Git index differs from the release file list')


def check_history(root, paths):
    check_index(root, paths)
    commits = subprocess.check_output(['git', '-C', str(root), 'rev-list', 'HEAD'], text=True).splitlines()
    for commit in commits:
        author, committer = subprocess.check_output(['git', '-C', str(root), 'show', '-s', '--format=%ae%n%ce', commit], text=True).splitlines()
        if not identity_allowed(author, committer):
            raise ValueError('Commit identity is not a GitHub noreply address')
        message = subprocess.check_output(['git', '-C', str(root), 'show', '-s', '--format=%B', commit])
        if findings(message):
            raise ValueError('Private content found in a commit message')
        names = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '--name-only', commit], text=True).splitlines()
        if not set(names).issubset(paths):
            raise ValueError('History contains files outside the release file list')
        for name in names:
            data = subprocess.check_output(['git', '-C', str(root), 'show', f'{commit}:{name}'])
            if findings(data):
                raise ValueError(f'Private content found in history: {name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, help='Copy reviewed files to a new directory')
    parser.add_argument('--archive', type=Path, help='Also scan a generated skill ZIP')
    parser.add_argument('--tracked', action='store_true', help='Require Git tracked files to match the public list')
    parser.add_argument('--history', action='store_true', help='Check tracked files and all reachable commits')
    args = parser.parse_args()
    try:
        paths = check(ROOT)
        if args.archive:
            check_archive(args.archive)
        if args.tracked:
            check_index(ROOT, paths)
        if args.history:
            check_history(ROOT, paths)
        if args.export:
            args.export.mkdir(parents=True, exist_ok=False)
            for name in paths:
                target = args.export / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
        print(f'Checked {len(paths)} public files. No configured privacy pattern matched.')
    except (ValueError, OSError, UnicodeError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
