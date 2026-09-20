import importlib.util
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_check', ROOT / 'scripts/release_check.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseChecks(unittest.TestCase):
    def test_all_public_content_passes(self):
        release.check(ROOT)

    def test_plain_text_paths_are_rejected_not_just_links(self):
        examples = ['/' + 'Users/person/project', '/' + 'home/person/project',
                    '/' + 'private/tmp/session', 'C:' + '\\Users\\person\\project']
        for value in examples:
            with self.subTest(value=value):
                self.assertTrue(release.findings(value.encode()))
        self.assertFalse(release.findings(b'project/.agents/skills/know-your-code/SKILL.md'))

    def test_credentials_and_private_email_are_rejected(self):
        examples = ['ghp_' + 'a' * 36, 'sk-' + 'b' * 40, 'person' + '@' + 'mail.example']
        for value in examples:
            self.assertTrue(release.findings(value.encode()))

    def test_archive_content_is_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'skill.zip'
            with ZipFile(archive, 'w') as output:
                for name in release.public_files(ROOT):
                    if name.startswith('skills/know-your-code/'):
                        output.writestr(Path(name).relative_to('skills').as_posix(), (ROOT / name).read_bytes())
                output.writestr('INSTALL.txt', '/' + 'Users/person/work')
            with self.assertRaises(ValueError):
                release.check_archive(archive)

    def test_incomplete_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'incomplete.zip'
            with ZipFile(archive, 'w') as output:
                output.writestr('harmless.txt', 'Nothing private here.')
            with self.assertRaises(ValueError):
                release.check_archive(archive)

    def test_manifest_refuses_escape_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'release-files.txt'
            manifest.write_text('../outside\n')
            with self.assertRaises(ValueError):
                release.public_files(root)
            (root / 'linked').symlink_to(ROOT / 'LICENSE')
            manifest.write_text('linked\n')
            with self.assertRaises(ValueError):
                release.public_files(root)
