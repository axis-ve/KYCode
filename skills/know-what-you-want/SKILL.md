---
name: know-what-you-want
description: Turn a rough idea into a request that can be built correctly the first time, by surfacing the decisions hidden inside it and settling most of them against the existing code. Use when the user describes something they want but cannot yet specify, when a previous attempt produced the wrong thing, when the user asks for help writing a prompt, spec, or ticket, or when they ask what they are not telling you. Do not use for routine tasks that are already clear.
---

# Know What You Want

A vague request is not a failure of the person asking. It is a request with decisions still inside it. Find those decisions, answer the ones the code already answers, and put the rest in front of the user in a form they can settle in a sentence.

## Use it when

- The user describes an outcome but not a behavior: "make the dashboard better," "add sharing," "handle errors properly."
- A previous attempt built the wrong thing and the user is about to try again.
- The user asks how to phrase a request, a ticket, or a prompt.
- The work is large enough that a wrong reading costs real time.

## Skip it when

- The request is already clear enough to act on. Build it. Clarification is not a ritual.
- One reasonable default covers every reading. State the assumption in one line and proceed.
- The user has said to stop asking and start building. That is their call; proceed under stated assumptions.

## Find the decisions

1. Read the code before asking anything. Most apparent ambiguity is already settled by what exists: the current shape of the data, the way similar features behave, the conventions the project follows.
2. Sort every open decision into three piles.
   - **The code decides.** Answer it yourself and say what the code said.
   - **A default decides.** Choose the least surprising option, state it, and let the user override.
   - **Only the user decides.** These are the questions. There are usually fewer than you expect.
3. Look specifically for the decisions that quietly change everything: who is allowed to do this, what happens to existing data, what the user sees when it fails, whether it has to work offline or under load, and whether anything outside this codebase depends on the current behavior.
4. Ask at most three questions at once, each with a recommended answer attached so agreement takes one word. Never ask something the code already answers.
5. Write the acceptance check before writing the code: the concrete observation that will prove this was built right. If you cannot state it, the request is still ambiguous.

Companion text can use this shape:

```markdown
## What you want
[one paragraph in the user's own words, tightened]

## Settled by the code
- [decision]: [answer, and the file that settled it]

## Assumed unless you say otherwise
- [decision]: [default]

## Need your call
1. [question] Recommended: [default].

## Done when
[the observable result, and the command or step that shows it]

## Not in scope
- [the nearby thing this deliberately does not do]
```

## Rules

- Never turn this into a questionnaire. Three questions, each answerable in a sentence, then build.
- Do not ask for information the repository contains. Looking it up is the work.
- Keep the user's own words in the summary. A specification they do not recognize is not their specification.
- Name what you are deliberately leaving out. Unstated scope is the other half of the misunderstanding.
- Proceed after the answers without asking for permission again. Approval to build was the point of asking.
- This skill plans; it does not build. Hand the settled request to the work itself, or to `know-your-code` if the next step is understanding rather than changing.
