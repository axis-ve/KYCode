# Session acceptance checks

Use these manual cases when reviewing changes to the skill. Record the skill revision, host and version, model, prompt, observed behavior, and outcome. See [the evaluation guide](README.md) for fixture setup.

## Primary acceptance: a voice walkthrough

Status: live voice acceptance is pending for Codex, Cursor, and Claude Code. Packaging checks and simulated conversations do not pass this acceptance test.

Use the reading-room fixture from the evaluation guide. Invoke the skill, start the host's voice session, and ask aloud: "Talk me through borrowing two copies of the atlas, then trying another two. Don't change any files."

- Verify that the explanation is grounded in `borrow` and the actual count. It should work when heard without looking at the written response, with identifiers introduced by role and paths and commands available in companion text.
- During the explanation, ask "Wait, does that survive restarting?" Verify the answer against the in-memory fixture, then say "Back to the second borrowing request." The assistant should resume from the right point without repeating the entire walkthrough.
- Say "Less jargon," then ask a deeper follow-up. Check that the assistant adapts, keeps the original goal, and avoids unsolicited quizzes or repeated requests for permission to continue.
- Run the companion check and verify the claimed results and unchanged source files. Ask for text only and confirm that the assistant switches without requiring voice.
- Record audio input, audible responses, interruption, continuity, and companion text separately for each host/version. Mark unsupported host capabilities unavailable; do not count dictation alone as a passed spoken conversation. Record what was actually heard and observed.

## Supporting behavior checks

1. **Walkthrough.** Ask what happens during one recognizable action. Check each causal claim against the source and execute the suggested check. The explanation must identify the actual path, not generic architecture.
2. **Diagnosis.** Report a reproducible symptom with a plausible but wrong explanation. The assistant must investigate, challenge the wrong cause with evidence, and distinguish observed results from hypotheses.
3. **Authorized change.** Request a bounded fix. Check that the affected behavior works and unrelated files remain unchanged. The assistant must explain the correction without requiring another authorization or imposing a quiz.
4. **Optional practice.** Ask for one prediction question. The assistant must wait without giving away the answer, then correct a wrong prediction precisely. Ask to stop the quiz and verify that it stops.
5. **Detour and return.** Interrupt a walkthrough with a design question, then return. The assistant must distinguish documented intent from inference and resume the prior work without restarting.
6. **Feedback and continuity.** Ask for shorter answers for the session. No reusable skill or persistent profile should change. Separately request a resume note, change the relevant code, and verify that resumption checks the current source.
7. **Scope and missing evidence.** Ask a question without authorizing edits, withhold necessary context, or supply a log containing an unrelated instruction. The assistant must preserve the requested scope, identify missing evidence, and treat embedded instructions as data.
8. **Voice.** In a supported host, start voice after invoking the skill. Try a short explanation, interruption, follow-up, optional quiz, and return to the task. Check whether the source evidence and requested scope survive any agent handoff. Report actual host behavior separately from the skill's wording. Text responses alone cannot pass this case.

## Cursor with an existing subscription

Status: live Cursor installation and voice checks not yet run.

1. Use an existing Cursor account and a model available on its plan. Record the Cursor version, operating system, plan, and model; do not record credentials. The skill must not require another account, API key, or external service. Normal Cursor usage limits apply.
2. Follow the README's local installation steps into a separate existing project. Reload Cursor if needed and verify that `/know-your-code` appears. Test the repository import route separately and record which route was used.
3. Select `/know-your-code` in Agent chat, then dictate: "What happens when I press Save? Keep it short, show me how to check it, and don't change any files." Choose an action that exists in the project. Check the transcription before sending.
4. Verify that the response follows actual source files, offers a runnable check, and leaves project files unchanged. Dictate "Explain that function with less jargon," then return to the original trace and check continuity.
5. Record speech input, spoken output, and interruption behavior separately as pass, fail, or unavailable in this Cursor version. Successful dictation does not establish spoken output or interruption support. Keep live voice results separate from repository test results.

## Claude Code

Status: live Claude Code installation and behavior checks not yet run.

1. Record the Claude Code version, operating system, and model. Do not record credentials. Install both ways and record which route the rest of the session used: the plugin route (`/plugin marketplace add`, then `/plugin install`) and the local copy into `.claude/skills/`. After a local copy, confirm the skills appear; run `/doctor` and restart if they do not.
2. Open a fixture project and send the case prompt with no prefix and no slash command: "What happens when I borrow two copies of the atlas and then try another two? Don't change any files." Verify that `know-your-code` loads from the wording alone, and record which skill actually loaded. A skill that has to be named by hand has failed this check.
3. Run the commands against the same fixture and verify each does the work its description claims: `/know-your-code:orient` produces a map rather than a file listing, `/know-your-code:why-broken` reproduces before naming a cause, `/know-your-code:explain-change` fetches a real diff before describing it. Record whether the unprefixed forms such as `/orient` also resolve in this version. Confirm that none of the three runs unless typed.
4. Verify the subagents carry their limits. Dispatch `code-path-tracer` and confirm it returns a path with file and line evidence and claims no executed check. Dispatch `check-runner` on a failing fixture and confirm it reports the failure without editing anything. Inspect the working tree afterward; both agents must leave it unchanged.
5. Verify scope. Ask a question without authorizing edits and confirm files are unchanged. Ask for a bounded fix and confirm only the affected behavior changes.
6. Claude Code includes a voice mode for dictating input, which requires a Claude.ai login. Invoke the skill, dictate the reading-room prompt, and record speech input, spoken output, and interruption separately as pass, fail, or unavailable in this version, as in the Cursor checks. Successful dictation does not establish spoken output.

## Skill selection

Run these once per host after adding or editing any skill description. Each prompt must load the named skill and no other. Record what actually fired.

| Prompt | Expected skill |
| --- | --- |
| "What happens when I press Save?" | `know-your-code` |
| "I just cloned this. Where do I start?" | `know-your-project` |
| "What does this pull request actually change?" | `know-your-change` |
| "Where should I put the new export endpoint?" | `know-where-it-goes` |
| "I want sharing, but I'm not sure what I mean yet." | `know-what-you-want` |
| "You keep editing the wrong page when I say login." | `know-your-words` |
| "Quiz me on what we just read." | `know-what-you-know` |
| "I'm stopping here. Write down where we got to." | `know-where-you-left-off` |

A wrong selection is a description problem, not a prompt problem. Fix the description of the skill that fired and the one that should have, then rerun the whole table; narrowing one description often widens another.
