---
description: Explain what a diff, commit, or PR actually changes
argument-hint: PR number, commit, branch, or nothing for the working tree
disable-model-invocation: true
---

# Explain Change

Use the `know-your-change` skill for this request. If it is not already loaded, invoke it by name, or read it at `${CLAUDE_PLUGIN_ROOT}/skills/know-your-change/SKILL.md`.

What to read:

$ARGUMENTS

If that is empty, read the uncommitted working tree, and say that is what you read.

## For this turn

- Get the real diff first with the repository's own tooling. A pull request number means fetching that pull request's diff; a commit or branch means comparing it against its base. Never summarize a change from its title or commit message.
- Read the code around each hunk, not just the hunk. Changed lines mean nothing without the function containing them and the callers reaching them.
- Group by behavior rather than by file, and lead with what a user of the software would notice. If the answer is "nothing, this is internal," say that first.
- Separate what changed from what it affects. Call out changed defaults, widened permissions, swapped dependencies, early returns on error paths, and data written in a new shape.
- Say what is now untested: behavior that changed without a corresponding test change.
- Do not approve or reject, and do not edit the change. Report what it does and what it risks; the decision is the user's.

End with what to run before trusting it.
