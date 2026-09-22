---
name: know-your-code
description: Voice-first code walkthroughs and debugging conversations grounded in the user's project. Use when the user wants to talk through how their app works, asks what happens when they press Save, wonders where edits go, reports a bug or symptom without pointing at a specific commit or pull request, or wants to understand a change they are asking for. Also works in text.
---

# Know Your Code

Help the user understand their code through a spoken conversation. Voice is the primary experience: follow one real user action, explain the causal path in language that works aloud, and support it with source references and a runnable check in companion text. Honor a user's choice to work in text.

## Lead a voice walkthrough

- Start from the action or symptom the user named. Inspect the relevant code before explaining it; give a brief, useful update when investigation takes time.
- Speak in connected, conversational sections, each covering one useful part of the path. Explain what happens and why before naming the implementation. Introduce an identifier by its role, then its name when useful.
- Keep file paths, code blocks, commands, and detailed logs in companion text when the host supports it. The spoken explanation must make sense without reading that text. Do not read Markdown headings or an arrow diagram aloud as the walkthrough.
- Leave room for steering at natural boundaries. On "less jargon," "go deeper," or a follow-up, adapt immediately. Do not require a quiz or ask permission to continue after every step.
- When the user interrupts or takes a detour, answer the new point while retaining the original action, verified evidence, and where to resume. On return, use a short bridge and continue without restarting the tour.
- If the user requests a quiz, ask one question and wait without revealing the answer. Otherwise continue the explanation naturally.
- Use the host's available voice session. Do not claim to start audio, hear unprovided input, or control playback or interruption. If another agent handles speech, pass the goal, scope, evidence, and resume point through available handoff tools. If voice is unavailable, state that briefly and offer the same walkthrough in text.

## Use it when

- The user names an action: press Save, refresh loses edits, delete needs confirmation, borrow two copies.
- The user reports a symptom and wants the cause in code.
- The user asks for a tour starting from something the app does.

## Skip it when

- The request is a routine implementation with no question about how the code works. Just do the task.
- The project files are unavailable. Ask for access or the relevant code instead of inventing a codebase.
- The user wants a map of a whole unfamiliar project rather than one action. Use `know-your-project` when it is installed.
- The user asks what a specific commit, branch, diff, or pull request does or broke. Use `know-your-change` when it is installed.

## Trace one action

1. Find the entry point by searching for the visible label, then the handler it calls. Prefer the label the user sees over architecture guesses.
2. Follow the handler through functions, requests, and stored data until the write or response. Read enough surrounding code to confirm each hop.
3. Explain the path conversationally using the voice guidance above. Put supporting evidence in a compact written companion using the shape below when helpful; adapt it for a text-only request. Keep files unchanged unless the user asked for a change.

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
- Ask one clarification at a time, only when the code cannot settle it. User-requested practice follows the quiz guidance above. Do not require a questionnaire or a lesson.
- For detail, read [reference.md](reference.md). For worked answers, read [examples.md](examples.md).
