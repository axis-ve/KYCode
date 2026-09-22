---
description: Find the cause of a symptom, reproduce it first
argument-hint: the symptom you are seeing
disable-model-invocation: true
---

# Why Broken

Use the `know-your-code` skill for this request, together with its diagnosis guidance at `${CLAUDE_PLUGIN_ROOT}/skills/know-your-code/reference.md`. If the skill is not already loaded, invoke it by name.

The reported symptom:

$ARGUMENTS

## For this turn

1. Reproduce before diagnosing. Use the project's own commands to make the symptom happen, or state plainly what blocks reproduction. Do not propose a cause you have not seen the code produce.
2. Read the code that the reproduction implicates. Compare it against the cause the user suggested, if they suggested one. A prompt often names the wrong function; keep the function that is already correct unchanged.
3. If two causes remain plausible, name the single observation that would tell them apart, then make that observation.
4. Report the cause, the evidence that establishes it, and the exact inputs and expected outputs that reproduce it, before proposing any edit.
5. Do not fix anything unless the user asked for a fix. If they did, keep the change inside the stated scope, exercise the real path rather than a helper, and say what the check proves and what it does not.

Dispatch the `check-runner` subagent to run reproductions and verification commands. It has no file-editing tools and is instructed not to change files through the shell, so it reports a failure instead of repairing it, along with exactly what was executed and what came back.
