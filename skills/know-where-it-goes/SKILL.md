---
name: know-where-it-goes
description: Decide where a new piece of code belongs in this repository, using the conventions the project already follows. Use when the user asks where to add something, which module or layer owns a concern, whether a file sits in the right place, how to fit a new feature into the existing structure, or where they would change a behavior later. Also works in text.
---

# Know Where It Goes

Answer placement questions from the repository's own precedents rather than from general architecture advice. Voice is the primary experience: name the place and the reason aloud, and keep paths and precedents in companion text.

## Use it when

- The user asks where to add a feature, a route, a model, a test, or a setting.
- The user asks which module owns a concern, or whether something is in the right layer.
- The user asks where they would change a behavior next time.

## Skip it when

- The user wants to know how something currently works. Use `know-your-code`.
- The user has not described the new thing well enough to place it. Use `know-what-you-want` first.
- The repository is empty or unavailable. Say so rather than proposing a structure for code that does not exist.

## Find the precedent

1. Name the kind of thing being added: a request handler, a background job, a validation rule, a stored field, a user-visible string.
2. Find two or three existing examples of that same kind in this repository. Precedent is the whole answer; a single example may be the outlier.
3. Read how those examples are wired: where they live, what registers them, what tests them, what names them. Placement includes registration, not just the file path.
4. Check the boundary the new code would cross. If it needs something from a layer that does not currently reach it, that is the real design question, and it is worth naming.
5. Propose one location, cite the precedent that supports it, and name the second-best option with the tradeoff that separates them.

## Say it in this order

Give the answer first: the directory or file and why it is the same kind of thing as its neighbors. Then what else has to change for it to be reachable. Then the smallest first step the user can take today.

Companion text can use this shape:

```markdown
## Put it here
`relative/path`

## Because
- `relative/path`: [the existing example this follows]

## Also wire up
- [registration, export, configuration, or test that makes it reachable]

## Alternative
[other location, and the tradeoff]

## First step
[the one file to create or open]
```

## Rules

- Read-only unless the user asks for the code. Deciding where something goes does not authorize writing it.
- Follow the repository's convention even when you would have chosen differently. Say once, briefly, if the convention has a real cost; then answer within it.
- Do not propose a new directory or layer unless no precedent exists, and say plainly that you are proposing one.
- If the repository is inconsistent, say which convention is more recent or more common, and base the answer on that.
- Do not require a refactor as the price of an answer. Give the placement that works in the code as it stands.
