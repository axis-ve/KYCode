# Contribute

For a bug report, include the prompt, expected behavior, observed behavior, and skill revision. Include the host and model when known, whether Codex, Cursor, or Claude Code. Use a synthetic example or a minimal reproduction you can share. Remove credentials, private project code, machine paths, and personal information before posting an issue.

## Check a change

Use Python 3.9 or newer. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/release_check.py
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

Repository tests check YAML, licenses, documentation links, the Cursor and Claude plugin manifests, the Claude commands and subagents, download contents, privacy detection, and fixture arithmetic. They do not run Codex, Cursor, or Claude Code, and they do not validate voice. Follow the [evaluation guide](evals/README.md) for behavioral changes. Report failures as well as successes.

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

Every folder under `skills/` is installable on its own. Keep each one's `LICENSE` identical to the root license, and give each one a `SKILL.md`, an `agents/openai.yaml`, and an `assets/logo.svg` so it stays branded and self-contained when copied alone. Generate downloadable ZIPs with `scripts/package_skill.py`; the archive carries every skill folder.

All three hosts read the same `skills/` tree. Codex copies the folders into `.agents/skills/`. Cursor copies them into `.cursor/skills/` or `~/.cursor/skills/`, and discovers them from the manifests in `.cursor-plugin/`. Claude Code copies them into `.claude/skills/` or `~/.claude/skills/`, and discovers them from `.claude-plugin/` along with the slash commands in `commands/` and the subagents in `agents/`. Those two directories are Claude-only; Codex and Cursor ignore them.

When adding a skill, give it a description that no existing skill would also match. Overlapping descriptions, not weak instructions, are the usual reason a skill fires on the wrong request. The repository test `test_skill_descriptions_stay_distinct` is a floor, not a substitute for reading them side by side.
