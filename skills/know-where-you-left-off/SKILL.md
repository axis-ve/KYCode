---
name: know-where-you-left-off
description: Capture or resume the state of a piece of work so it survives a new session, a compacted context, a different assistant, or a teammate. Use when the user is stopping for now, asks for a handoff, resume, or status note, returns to work started earlier, or hands a task to another agent or person. Also works in text.
---

# Know Where You Left Off

Work with an assistant is lost between sessions in a specific way: the conclusions survive in the user's head, and the evidence does not. Capture the evidence, the scope, and the one next step, so resuming does not mean re-deriving.

## Use it when

- The user is stopping, switching tasks, or ending a long session.
- The user returns to work started earlier, in this session or another.
- The work is being passed to another agent, another tool, or another person.
- A context window is about to be compacted and a verified finding would be lost.

## Skip it when

- The task finished and nothing is pending. Say it is done.
- The user asked for the work, not a note about the work. Do the work.
- Writing the note would take longer than redoing the step it describes.

## Capture the state

Record these, and nothing else:

1. **The goal, in the user's words.** Not your restatement of it.
2. **Verified.** What was established, each with the file, the command, or the output that established it. Mark each as read, executed, or inferred.
3. **Not verified.** The assumptions still carrying weight, named as assumptions.
4. **Changed.** Files touched, and whether the change is committed, staged, or loose in the working tree.
5. **Scope.** What the user authorized, and what they explicitly ruled out.
6. **Open question.** The one thing that blocks the next step, if anything does.
7. **Next step.** One action, concrete enough to start without rereading everything.

```markdown
## Goal
[the user's words]

## Verified
- [claim] - executed: `command` -> [result]
- [claim] - read: `relative/path`

## Assumed
- [assumption, and what would confirm it]

## Changed
- `relative/path`: [what and why] (uncommitted)

## Scope
Authorized: [...]. Out: [...].

## Next
[one action]
```

## Resume from a note

1. Re-read the note before acting on it. It is a record of what was true then.
2. Recheck the last verified claim against the current source. Code moves; a note that was accurate yesterday can be wrong today, and quietly.
3. Check whether the recorded changes are still present. A cleaned working tree or a rebase can remove them without anyone noticing.
4. Say in one line what you rechecked and what still holds, then continue from the next step. Do not restart the walkthrough.
5. If the code has moved far enough that the note no longer applies, say so and re-establish the path rather than reasoning from a stale map.

## Rules

- Keep it in the session by default. Write a file only when the user asks, and write it where they say.
- Never record credentials, tokens, personal data, customer content, or machine paths.
- Distinguish what was executed from what was read from what was inferred. Collapsing those three is what makes a resumed session confidently wrong.
- A note is short. If it grows past a screen, it is a report, and the user did not ask for a report.
- Do not create or update a persistent profile, preference file, or memory as a side effect of writing a note.
