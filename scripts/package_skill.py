"""Build an installable ZIP from the skill folder."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]



def package(output):
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        files = [(Path(name).relative_to('skills').as_posix(), (ROOT / name).read_bytes())
                 for name in (ROOT / 'release-files.txt').read_text().splitlines()
                 if name.startswith('skills/know-your-code/')]
        for name, data in files + [('INSTALL.txt', (ROOT / 'INSTALL.txt').read_bytes())]:
            entry = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    package(args.output)
    print(args.output)
