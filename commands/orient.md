---
description: Map an unfamiliar repository before you dive in
argument-hint: optional area to focus on
disable-model-invocation: true
---

# Orient

Use the `know-your-project` skill for this request. If it is not already loaded, invoke it by name, or read it at `${CLAUDE_PLUGIN_ROOT}/skills/know-your-project/SKILL.md`.

Focus, if the user gave one:

$ARGUMENTS

## For this turn

- Read what the project says about itself first: the readme, the package or build manifest, and the scripts it defines. Treat those as claims until the code agrees.
- Find two or three real ways in rather than a complete inventory: a main entry file, a route table or command parser, a user interface root, a scheduled job.
- Find where state lives and what writes to it, and find the install, start, and test commands. Mark each command as read or executed; do not run anything that installs, migrates, or deploys without asking.
- Stop when the user could open one file and know what they are looking at.

If the repository is large, dispatch several `code-path-tracer` subagents in parallel, one per candidate entry point, and assemble their reports into one map. Each is read-only, so the search cannot change anything, and the raw file dumps stay out of this conversation.

Deliver the map in the shape the skill describes, then offer one next step: the single action most worth tracing in depth with `/know-your-code`.
