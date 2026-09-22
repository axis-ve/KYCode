import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from zipfile import ZipFile

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills'
SKILL = SKILLS / 'know-your-code'
RELEASE = (ROOT / 'release-files.txt').read_text().splitlines()
PUBLIC_SKILL_FILES = [name for name in RELEASE if name.startswith('skills/')]
SKILL_NAMES = sorted({Path(name).parts[1] for name in PUBLIC_SKILL_FILES})
HOST_SKILL_DIRS = ('.agents/skills', '.cursor/skills', '.claude/skills')
AGENT_TOOLS = {'Read', 'Glob', 'Grep', 'Bash'}
NO_EDIT_CLAIM = r"(?i)\b(cannot|can't|can not|unable to|is not able to)\s+(edit|write|change|modify|create)\b|\bread-only\b"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'evals/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frontmatter(path):
    text = path.read_text()
    if not text.startswith('---\n'):
        raise ValueError(f'Missing frontmatter: {path}')
    return yaml.safe_load(text.split('---', 2)[1])


class PackageChecks(unittest.TestCase):
    def test_download_contains_every_installable_skill(self):
        spec = importlib.util.spec_from_file_location('package_skill', ROOT / 'scripts/package_skill.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = {Path(name).relative_to('skills').as_posix() for name in PUBLIC_SKILL_FILES}
        expected.add('INSTALL.txt')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'skill.zip'
            module.package(output)
            with ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), expected)
                self.assertIn('know-your-code/SKILL.md', expected)
                for path in (path for path in SKILLS.rglob('*') if path.is_file()):
                    self.assertEqual(archive.read(path.relative_to(SKILLS).as_posix()), path.read_bytes())
                for host in HOST_SKILL_DIRS:
                    installed = Path(directory) / 'project' / host
                    archive.extractall(installed)
                    for name in SKILL_NAMES:
                        self.assertTrue((installed / name / 'SKILL.md').is_file(), f'{host}/{name}')

    def test_every_skill_carries_metadata_licence_and_branding(self):
        self.assertIn('know-your-code', SKILL_NAMES)
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                folder = SKILLS / name
                metadata = frontmatter(folder / 'SKILL.md')
                self.assertEqual(metadata['name'], name)
                self.assertIsInstance(metadata['description'], str)
                self.assertTrue(1 <= len(metadata['description']) <= 1024)
                self.assertEqual((folder / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
                ui = yaml.safe_load((folder / 'agents/openai.yaml').read_text())['interface']
                self.assertIn('$' + name, ui['default_prompt'])
                self.assertTrue(25 <= len(ui['short_description']) <= 64)
                for field in ('icon_small', 'icon_large'):
                    icon = (folder / ui[field]).resolve()
                    self.assertTrue(icon.is_relative_to(folder.resolve()))
                    self.assertTrue(icon.is_file())
                self.assertRegex(ui['brand_color'], r'^#[0-9A-Fa-f]{6}$')

    def test_skill_descriptions_stay_distinct(self):
        """Overlapping descriptions are the usual cause of a skill firing on the wrong request."""
        descriptions = {name: frontmatter(SKILLS / name / 'SKILL.md')['description'] for name in SKILL_NAMES}
        self.assertEqual(len(set(descriptions.values())), len(SKILL_NAMES))
        for name, description in descriptions.items():
            with self.subTest(skill=name):
                self.assertRegex(description, r'\bUse when\b|\bUse it when\b')

    def test_cursor_plugin_discovers_the_same_skills(self):
        plugin = json.loads((ROOT / '.cursor-plugin/plugin.json').read_text())
        marketplace = json.loads((ROOT / '.cursor-plugin/marketplace.json').read_text())
        self.assertEqual(plugin['name'], SKILL.name)
        self.assertEqual(plugin['license'], 'MIT')
        self.assertEqual((ROOT / plugin['logo']).read_bytes(), (SKILL / 'assets/logo.svg').read_bytes())
        skills_root = (ROOT / plugin['skills']).resolve()
        self.assertEqual(skills_root, SKILLS.resolve())
        for name in SKILL_NAMES:
            self.assertTrue((skills_root / name / 'SKILL.md').is_file())
        self.assertEqual(marketplace['name'], SKILL.name)
        self.assertEqual([entry['name'] for entry in marketplace['plugins']], [SKILL.name])
        self.assertEqual(marketplace['plugins'][0]['source'], '.')

    def test_claude_plugin_discovers_the_same_skills(self):
        plugin = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
        marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(plugin['name'], SKILL.name)
        self.assertEqual(plugin['license'], 'MIT')
        self.assertEqual(marketplace['name'], SKILL.name)
        self.assertEqual([entry['name'] for entry in marketplace['plugins']], [SKILL.name])
        entry = marketplace['plugins'][0]
        self.assertEqual(entry['source'], '.')
        # Claude Code discovers plugin components by convention from the plugin root.
        self.assertEqual((ROOT / entry['source'] / 'skills').resolve(), SKILLS.resolve())
        for name in SKILL_NAMES:
            self.assertTrue((ROOT / 'skills' / name / 'SKILL.md').is_file())

    def test_host_manifests_agree_on_version_and_description(self):
        plugins = [json.loads((ROOT / f'{host}/plugin.json').read_text()) for host in ('.claude-plugin', '.cursor-plugin')]
        claude_market = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        cursor_market = json.loads((ROOT / '.cursor-plugin/marketplace.json').read_text())
        self.assertEqual(plugins[0]['version'], plugins[1]['version'])
        self.assertRegex(plugins[0]['version'], r'^\d+\.\d+\.\d+$')
        descriptions = {plugin['description'] for plugin in plugins}
        descriptions |= {claude_market['plugins'][0]['description'], cursor_market['plugins'][0]['description']}
        self.assertEqual(len(descriptions), 1)
        self.assertEqual(claude_market['description'], cursor_market['metadata']['description'])

    def test_claude_commands_and_agents_are_well_formed(self):
        commands = sorted((ROOT / 'commands').glob('*.md'))
        agents = sorted((ROOT / 'agents').glob('*.md'))
        self.assertTrue(commands and agents)
        # Claude Code registers commands as skills, so a shared name would appear twice.
        self.assertFalse({path.stem for path in commands} & set(SKILL_NAMES))
        for path in commands:
            with self.subTest(command=path.name):
                metadata = frontmatter(path)
                self.assertTrue(1 <= len(metadata['description']) <= 60)
                self.assertIsInstance(metadata['argument-hint'], str)
                # Commands are explicit entry points; the skills own automatic routing.
                self.assertIs(metadata.get('disable-model-invocation'), True)
                body = path.read_text()
                self.assertIn('$ARGUMENTS', body)
                for reference in re.findall(r'`([^`]*skills/[^`]*)`', body):
                    self.assertTrue(reference.startswith('${CLAUDE_PLUGIN_ROOT}'),
                                    f'{reference} resolves against the user project, not the plugin')
        for path in agents:
            with self.subTest(agent=path.name):
                metadata = frontmatter(path)
                self.assertEqual(metadata['name'], path.stem)
                self.assertIsInstance(metadata['description'], str)
                tools = {tool.strip() for tool in metadata['tools'].split(',')}
                self.assertLessEqual(tools, AGENT_TOOLS, 'Agents get read, search, and shell tools only')
                if 'Bash' in tools:
                    self.assertNotRegex(path.read_text(), NO_EDIT_CLAIM,
                                        'A shell can write files, so that limit is an instruction, not a tool restriction')

    def test_documentation_names_every_host_and_entry_point(self):
        readme = (ROOT / 'README.md').read_text()
        install = (ROOT / 'INSTALL.txt').read_text()
        for marker in ('$skill-installer', '.cursor/skills', '.claude/skills', '/know-your-code'):
            self.assertIn(marker, readme)
        for host in HOST_SKILL_DIRS:
            self.assertIn(f'{host}/know-your-code/SKILL.md', install)
        for name in SKILL_NAMES:
            self.assertIn(name, readme)

    def test_documentation_links_resolve_without_local_machine_paths(self):
        paths = [ROOT / 'README.md', ROOT / 'CONTRIBUTING.md']
        paths += list((ROOT / 'evals').rglob('*.md')) + list(SKILLS.rglob('*.md'))
        paths += list((ROOT / 'commands').glob('*.md')) + list((ROOT / 'agents').glob('*.md'))
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
            for host in HOST_SKILL_DIRS:
                self.assertEqual((project / host / 'know-your-code/SKILL.md').read_bytes(),
                                 (SKILL / 'SKILL.md').read_bytes())
                for name in SKILL_NAMES:
                    self.assertTrue((project / host / name / 'SKILL.md').is_file())
            self.assertEqual(len((project / 'noisy.log').read_text().splitlines()), 82)
            manifest = json.loads((destination / 'run.json').read_text())
            self.assertEqual(sorted(manifest['skills_sha256']), SKILL_NAMES)
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
