"""Prepare an isolated checkout fixture without running an agent."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import shutil

ROOT = Path(__file__).resolve().parents[1]


def prepare(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    project = destination / 'project'
    project.mkdir()
    fixture = ROOT / 'evals/fixtures/checkout/cart.py'
    shutil.copy2(fixture, project / 'cart.py')
    skill = ROOT / 'skills/know-your-code'
    shutil.copytree(skill, project / '.agents/skills/know-your-code')
    shutil.copytree(skill, project / '.cursor/skills/know-your-code')
    cart = runpy.run_path(str(project / 'cart.py'))
    lines = [f'DEBUG synthetic heartbeat {i:02d}' for i in range(80)]
    lines[60:60] = [f"display={cart['display_price']('tea')}",
                    f"checkout={cart['checkout_payload']('tea', 1)}"]
    (project / 'noisy.log').write_text('\n'.join(lines) + '\n')
    manifest = {
        'prepared_at': datetime.now(timezone.utc).isoformat(),
        'status': 'not run',
        'skill_sha256': hashlib.sha256((skill / 'SKILL.md').read_bytes()).hexdigest(),
        'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'model': None,
        'host_and_version': None,
        'other_active_instructions': None,
        'case': None,
        'response_and_tool_record': None,
        'reviewer': None,
        'outcome': None,
    }
    (destination / 'run.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return project


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='A new directory; existing paths are refused')
    args = parser.parse_args()
    try:
        print(prepare(args.destination))
    except FileExistsError:
        parser.error('Destination already exists; choose a new directory to preserve previous evidence.')
