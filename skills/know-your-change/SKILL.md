---
name: know-your-change
description: Explain what a diff, commit, branch, or pull request actually changes, read against the code around it. Use when the user asks what a change does, wants a review they can follow, asks what to test before merging, is catching up on someone else's work, or wonders why a recent change broke something. Also works in text.
---

# Know Your Change

Explain a change in terms of behavior the user recognizes, not in terms of the lines that moved. Voice is the primary experience: say what is different now and what that means, and keep hunks, paths, and commands in companion text.

## Use it when

- The user asks what a pull request, commit, branch, or working-tree diff does.
- The user wants to understand someone else's change before approving or merging it.
- The user asks what to test, or what could break, because of a change.

## Skip it when

- The user asked for a defect hunt with a verdict. That is a code review; do that directly.
- The user reported a symptom without pointing at a change. Use `know-your-code` to find the cause first.
- No diff is available. Ask which change to read rather than summarizing recent history from memory.

## Read the change

1. Get the actual diff with the project's own tools before saying anything about it. Use the repository's history, the branch comparison, or the pull request contents. If a hosted pull request is named and the host tooling is available, read it; otherwise ask for the branch or commit range.
2. Read the code around each hunk, not only the hunk. A changed line means nothing without the function that contains it and the callers that reach it.
3. Group the change by behavior, not by file. Several files that serve one behavior belong in one section.
4. Separate what changed from what it affects. A renamed helper changes nothing; a changed default changes every caller that relied on it.
5. Identify what is untested. Look for a corresponding test change; if none exists, say which behavior now rests on nothing.

## Say it in this order

Lead with what a user of the software would notice. Then the mechanism that produces it. Then the parts worth attention: a changed default, a widened permission, a swapped dependency, an error path that now returns early, data written in a new shape. End with what to run before trusting it.

Companion text can use this shape:

```markdown
## What changes for the user
[observable difference, or "none, this is internal"]

## How
- `relative/path`: [what this file contributes]

## Worth attention
- [risk, and the specific line or behavior that creates it]

## Test before merging
[commands or steps that exercise the changed path]
```

## Rules

- Read-only unless the user asks for changes. Explaining a change does not authorize editing it.
- Do not approve or reject. Report what the change does and what it risks; the decision is the user's.
- Do not guess intent from a commit message. Say what the code does, and mark stated intent as a claim.
- Say when a change is larger than it looks, and when it is smaller: a thousand-line diff that only reformats deserves one sentence.
- If the diff touches generated files, lockfiles, or vendored code, separate them out rather than reading them line by line.
