---
name: know-your-code
description: Traces one user action through the codebase from UI label to handler to stored data, diagnoses bugs with source evidence and runnable checks, and verifies requested fixes. Use when the user asks what happens when they press Save, where edits go, why a symptom occurs, or wants a codebase tour grounded in project files.
---

# Know Your Code

Follow one user action through the project's actual code and show how to check it.

## Use it when

- The user names an action: press Save, refresh loses edits, delete needs confirmation, borrow two copies.
- The user reports a symptom and wants the cause in code.
- The user asks for a tour starting from something the app does.

## Skip it when

- The request is a routine implementation with no question about how the code works. Just do the task.
- The project files are unavailable. Ask for access or the relevant code instead of inventing a codebase.

## Trace one action

1. Find the entry point by searching for the visible label, then the handler it calls. Prefer the label the user sees over architecture guesses.
2. Follow the handler through functions, requests, and stored data until the write or response. Read enough surrounding code to confirm each hop.
3. Answer with the output shape below. Keep files unchanged unless the user asked for a change.

```markdown
## Path
[user action] -> [handler] -> [storage or response]

## Stored data
[what changed, where, in what shape]

## Files
- `relative/path.py`: [role in this trace]

## Check
[one runnable command or step that proves the path]
```

## Rules

- Exploration is read-only unless the user asks for changes. A fix request authorizes that fix within its stated scope.
- Separate what you read, what you ran, and what you infer. Challenge a proposed diagnosis when the code disagrees.
- Do not invent files, runs, or historical intent. Label illustrative examples and tie them back to the real code.
- Ask at most one question, and only when the code cannot settle it. Do not require a questionnaire or a lesson.
- For detail, read [reference.md](reference.md). For worked answers, read [examples.md](examples.md).
