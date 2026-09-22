---
name: know-your-project
description: Build a first map of an unfamiliar codebase, covering what it does, how to run it, where the entry points are, where state lives, and what to read first. Use when the user has just cloned or inherited a repository, asks where to start, wants a tour of the whole project rather than one feature, or asks how the pieces fit together. Also works in text.
---

# Know Your Project

Give the user a map they can navigate from, built by reading the repository rather than by guessing from its name. Voice is the primary experience: describe the shape of the project in language that works aloud, and keep paths, commands, and structure in companion text.

## Use it when

- The user just cloned, inherited, or returned to a repository and asks where to start.
- The user asks what the project is, how to run it, or how the parts fit together.
- The user wants a tour before naming a specific feature to trace.

## Skip it when

- The user already named one action or symptom. Trace that instead with `know-your-code`.
- The user asked where a new piece of code belongs. Use `know-where-it-goes`.
- The project files are unavailable. Ask for access rather than describing a codebase you cannot read.

## Build the map

1. Read what the project says about itself: the readme, the package or build manifest, and the scripts or tasks it defines. Note what it claims, and treat it as a claim until the code agrees.
2. Find the ways in. Look for a main entry file, a server or route table, a command-line parser, a user interface root, and scheduled or background jobs. Two or three real entry points beat a complete inventory.
3. Find where state lives: database models or migrations, a schema file, the directory written at runtime, the cache, the configuration the code actually reads.
4. Find how it runs and how it is checked: the install step, the start command, the test command. Say which of these you ran and which you only read.
5. Stop when the user could open one file and understand what they are looking at. Do not index the whole repository.

## Say it in this order

Lead with what the project does for its user, then the one path through it that matters most, then where the user should look first. Name a directory by its job before its path. Keep the map short enough to hold in one conversation, and offer to trace any single entry point in depth.

Companion text can use this shape:

```markdown
## What it is
[one or two sentences, grounded in what the code does]

## Ways in
- `relative/path`: [what enters here]

## Where state lives
[store, schema or file, and what writes to it]

## Run it
[install, start, and test commands, marked as read or executed]

## Read these first
1. `relative/path`: [why this one]
```

## Rules

- Exploration is read-only. Do not modify, reformat, or "clean up" anything while mapping.
- Separate what you read from what you ran from what you infer. If the readme and the code disagree, say so and trust the code.
- Name what you could not find. A missing test command or an unreadable directory is part of the map.
- Do not invent architecture. If the project has no clear layering, say that plainly instead of imposing a pattern on it.
- In a large repository, say which area the map covers and which it leaves out. A partial map presented as complete is worse than no map.
- Offer one next step rather than a syllabus: the single action most worth tracing first.
