"""Check the notes-app title fix and the features that share its helper. This does not grade an assistant response."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

SCENARIO = """
import json, app, notes
note_id = app.press("Save", title="My  Plans", body="Ship it")
print(json.dumps({
    "saved": notes.get_note(note_id)["title"],
    "search_lower": app.press("Search", query="plans"),
    "search_upper": app.press("Search", query="PLANS"),
    "export": app.press("Export", note_id=note_id)[0],
}))
"""


def run(project):
    result = subprocess.run([sys.executable, '-B', '-c', SCENARIO], cwd=project, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f'Scenario failed: {result.stderr.strip().splitlines()[-1]}')
    return json.loads(result.stdout)


def check(project, expected):
    outputs = run(project)
    title = 'my plans' if expected == 'buggy' else 'My Plans'
    if outputs['saved'] != title:
        raise ValueError(f"Saved title: expected {title!r}, got {outputs['saved']!r}")
    for key in ('search_lower', 'search_upper'):
        if outputs[key] != [title]:
            raise ValueError(f'Search must stay case-insensitive: {key} expected {[title]}, got {outputs[key]}')
    if outputs['export'] != 'my-plans.md':
        raise ValueError(f"Export filename must stay 'my-plans.md', got {outputs['export']!r}")
    return outputs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--expect', choices=['buggy', 'fixed'], required=True)
    args = parser.parse_args()
    try:
        print(check(args.project, args.expect))
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
