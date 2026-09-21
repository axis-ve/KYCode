import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from zipfile import ZipFile

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/know-your-code'


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'evals/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackageChecks(unittest.TestCase):
    def test_download_contains_complete_installable_skill(self):
        spec = importlib.util.spec_from_file_location('package_skill', ROOT / 'scripts/package_skill.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'skill.zip'
            module.package(output)
            with ZipFile(output) as archive:
                files = [path for path in SKILL.rglob('*') if path.is_file()]
                self.assertEqual(set(archive.namelist()), {
                    'know-your-code/SKILL.md', 'know-your-code/LICENSE',
                    'know-your-code/agents/openai.yaml', 'know-your-code/assets/logo.svg', 'INSTALL.txt',
                })
                for path in files:
                    self.assertEqual(archive.read(path.relative_to(SKILL.parent).as_posix()), path.read_bytes())
                installed = Path(directory) / 'project/.agents/skills'
                archive.extractall(installed)
                self.assertTrue((installed / 'know-your-code/SKILL.md').is_file())
                cursor_installed = Path(directory) / 'project/.cursor/skills'
                archive.extractall(cursor_installed)
                self.assertTrue((cursor_installed / 'know-your-code/SKILL.md').is_file())

    def test_skill_metadata_and_license(self):
        text = (SKILL / 'SKILL.md').read_text()
        self.assertTrue(text.startswith('---\n'))
        metadata = yaml.safe_load(text.split('---', 2)[1])
        self.assertEqual(metadata['name'], SKILL.name)
        self.assertIsInstance(metadata['description'], str)
        self.assertTrue(1 <= len(metadata['description']) <= 1024)
        self.assertEqual((SKILL / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
        ui = yaml.safe_load((SKILL / 'agents/openai.yaml').read_text())['interface']
        self.assertIn('$' + metadata['name'], ui['default_prompt'])
        self.assertTrue(25 <= len(ui['short_description']) <= 64)
        for field in ('icon_small', 'icon_large'):
            icon = (SKILL / ui[field]).resolve()
            self.assertTrue(icon.is_relative_to(SKILL.resolve()))
            self.assertTrue(icon.is_file())
        self.assertRegex(ui['brand_color'], r'^#[0-9A-Fa-f]{6}$')

    def test_cursor_plugin_discovers_the_same_skill(self):
        plugin = json.loads((ROOT / '.cursor-plugin/plugin.json').read_text())
        marketplace = json.loads((ROOT / '.cursor-plugin/marketplace.json').read_text())
        self.assertEqual(plugin['name'], SKILL.name)
        self.assertEqual(plugin['license'], 'MIT')
        self.assertEqual((ROOT / plugin['logo']).read_bytes(), (SKILL / 'assets/logo.svg').read_bytes())
        skills_root = (ROOT / plugin['skills']).resolve()
        self.assertEqual(skills_root, SKILL.parent.resolve())
        self.assertTrue((skills_root / SKILL.name / 'SKILL.md').is_file())
        self.assertEqual(marketplace['name'], SKILL.name)
        self.assertEqual([entry['name'] for entry in marketplace['plugins']], [SKILL.name])
        self.assertEqual(marketplace['plugins'][0]['source'], '.')
        readme = (ROOT / 'README.md').read_text()
        self.assertIn('/know-your-code', readme)
        self.assertIn('.cursor/skills', readme)
        self.assertIn('$skill-installer', readme)
        install = (ROOT / 'INSTALL.txt').read_text()
        self.assertIn('.agents/skills/know-your-code/SKILL.md', install)
        self.assertIn('.cursor/skills/know-your-code/SKILL.md', install)

    def test_documentation_links_resolve_without_local_machine_paths(self):
        paths = [ROOT / 'README.md', ROOT / 'CONTRIBUTING.md']
        paths += list((ROOT / 'evals').rglob('*.md')) + list(SKILL.rglob('*.md'))
        for path in paths:
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if target.startswith(('https://', 'http://', '#')):
                    continue
                with self.subTest(file=path.relative_to(ROOT), target=target):
                    self.assertFalse(Path(target).is_absolute(), 'Machine-local Markdown link')
                    resolved = (path.parent / target.split('#')[0]).resolve()
                    self.assertTrue(resolved.is_relative_to(ROOT))
                    self.assertTrue(resolved.exists(), 'Missing link target')


class FixtureChecks(unittest.TestCase):
    def test_fresh_fixture_rejects_fixed_claim_and_accepts_real_fix(self):
        prepare = load_script('prepare').prepare
        check = load_script('check_fixture').check
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'case'
            project = prepare(destination)
            self.assertEqual((project / '.agents/skills/know-your-code/SKILL.md').read_bytes(),
                             (SKILL / 'SKILL.md').read_bytes())
            self.assertEqual((project / '.cursor/skills/know-your-code/SKILL.md').read_bytes(),
                             (SKILL / 'SKILL.md').read_bytes())
            self.assertEqual(len((project / 'noisy.log').read_text().splitlines()), 82)
            check(project, 'buggy')
            with self.assertRaises(ValueError):
                check(project, 'fixed')
            original = (project / 'cart.py').read_text()
            (project / 'cart.py').write_text(original.replace(' * quantity * 100', ' * quantity'))
            check(project, 'fixed')
            with self.assertRaises(ValueError):
                check(project, 'buggy')
            with self.assertRaises(FileExistsError):
                prepare(destination)
            self.assertNotEqual((project / 'cart.py').read_text(), original)
