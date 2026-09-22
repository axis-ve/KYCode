# Test the skill

Use these examples to check a skill change in Codex, Cursor, or Claude Code. Each fixture is a small Python project with a known result. Python 3.9 or newer is required.

Voice is the primary acceptance path. Start with the [voice walkthrough checks](session-checks.md), using these fixtures for source evidence. Run text-only cases as regression checks. Passing repository tests or reviewing a transcript does not establish a working spoken conversation.

## Set up a case

1. Copy a folder from [fixtures](fixtures) into a new working directory outside this repository.
2. Copy the folders in `skills/` into that directory's `.agents/skills/` for Codex, `.cursor/skills/` for Cursor, or `.claude/skills/` for Claude Code.
3. Open the directory in the host and start a new task.
4. Send the case's prompt below. In Cursor, type `/know-your-code` instead of `$know-your-code`. In Claude Code, drop the prefix and send the request on its own, so the case also checks that the right skill loads from the wording alone. In the optional-question case, `know-your-code` and `know-what-you-know` are both correct, since both ask one question and wait; record which one loaded. Keep the expected results separate from the host task.

Use a fresh copy for each case. Afterward, compare the explanation with the source, inspect file changes, and run the affected code.

## Trace a feature

Fixture: [reading-room/library.py](fixtures/reading-room/library.py).

```text
$know-your-code Walk me through what happens when I borrow two copies of the atlas and then try another two. Keep it short, show me how to check it, and don't change any files.
```

Expected results:

- The assistant reads `library.py` and follows `borrow`.
- The first call returns `True` and leaves one copy.
- The second call returns `False` and leaves the count unchanged.
- The explanation includes a runnable check. Source files remain unchanged.

## Diagnose and fix a bug

Fixture: [parcel-room/shipping.py](fixtures/parcel-room/shipping.py).

```text
$know-your-code The label formatter is broken: a small parcel displays $4.50 but the quote asks for $450. Fix it. One small parcel should be $4.50, two should be $9.00, and one large should be $9.00. Check the result and explain the change briefly.
```

The prompt deliberately suggests the wrong cause. Expected results:

- The assistant identifies the extra multiplication by 100 in `quote`.
- The fix preserves the correct `label` function.
- Executed checks confirm quotes of 450, 900, and 900 cents for the three cases.
- The explanation identifies the unit error and the correction.

## Ask an optional question

Fixture: [drawing-room/canvas.py](fixtures/drawing-room/canvas.py).

```text
$know-your-code Help me understand the preview function. Read the code, then ask me one question about what it returns for a 120 by 80 canvas. Don't reveal the answer yet. Don't edit or save anything.
```

Expected results:

- The assistant reads the source, asks one question, and waits for an answer.
- It does not disclose the dimensions before the user responds.
- If the user answers `240 by 160`, it explains that the scale is 0.5 and the result is `60 by 40`.
- Source files remain unchanged.

## Check the checkout fixture

The checkout fixture includes a currency conversion bug and a synthetic log. Prepare a copy and verify its initial state:

```sh
python3 evals/prepare.py ./scratch-checkout
python3 evals/check_fixture.py ./scratch-checkout/project --expect buggy
```

After asking the assistant to fix the bug, check the result:

```sh
python3 evals/check_fixture.py ./scratch-checkout/project --expect fixed
```

Preparation refuses an existing destination. These commands check the arithmetic; review the conversation separately.

## Report a result

Include the skill commit, host and version, model, prompt, observed behavior, and file changes. Mark each expected result as pass, fail, or not tested. Use synthetic examples and remove private data before sharing a report.

See [session acceptance checks](session-checks.md) for detours, feedback, scope, and voice. Repository checks are listed in [Contributing](../CONTRIBUTING.md). Automated checks cover packaging, manifests, and fixtures; they do not measure teaching quality. Live voice testing is pending.
