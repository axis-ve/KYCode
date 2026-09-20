# Contribute

For a bug report, include the prompt, expected behavior, observed behavior, and skill revision. Include the Codex host and model when known. Use a synthetic example or a minimal reproduction you can share. Remove credentials, private project code, machine paths, and personal information before posting an issue.

## Check a change

Use Python 3.9 or newer. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/release_check.py
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

Repository tests check YAML, licenses, documentation links, download contents, privacy detection, and fixture arithmetic. They do not run Codex or validate voice. Follow the [evaluation guide](evals/README.md) for behavioral changes. Report failures as well as successes.

## Keep the skill focused

Keep changes focused on helping users understand and work on their code. Include an example prompt and the behavior your change addresses. The skill must remain usable without another skill pack.

## Prepare a release

`release-files.txt` is the public file list. Add new public files there deliberately. The export refuses existing destinations and excludes everything not listed, including development history.

```sh
python3 scripts/package_skill.py ./know-your-code.zip
python3 scripts/release_check.py --archive ./know-your-code.zip
python3 scripts/release_check.py --export ./release-copy
```

Inspect the resulting files and ZIP. The scanner detects configured patterns, not every possible secret or private fact. Review prose, examples, filenames, and metadata too. Keep transcripts and internal reports out of the public file list.

To scan tracked files and reachable commits, run `python3 scripts/release_check.py --history`. This check requires GitHub noreply commit email addresses and rejects historical files outside the current release list.

The installable folder is `skills/know-your-code/`. Keep its `LICENSE` identical to the root license. Generate downloadable ZIPs with `scripts/package_skill.py`.
