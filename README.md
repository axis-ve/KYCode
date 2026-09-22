![Know Your Code. Your code. Your aha. Less guessing, more getting it.](assets/cover.png)

<h1 align="center">Know Your Code</h1>

A voice-first skill for talking through how your app works, finding why it breaks, and making changes you can maintain. It works in Codex, Cursor, and Claude Code from the same instructions.

Start with something your app does and talk it through: "What happens when I press Save?" The assistant follows the actual code, explains it in conversational sections, and keeps file references and runnable checks in companion text. Interrupt with "less jargon," explore a side question, then return to the walkthrough without starting over. Text-only use is supported too.

## Install

### Codex

Send this in Codex:

```text
$skill-installer Install https://github.com/axis-ve/KYCode/tree/main/skills/know-your-code
```

That installs the main skill. To add a companion skill, run the same command with its folder name in place of `know-your-code`, for example `skills/know-your-project`. The [skill list](#the-skills) names all eight.

Open your project in Codex, then send:

```text
$know-your-code What happens when I press Save?
Follow it from the button to storage. Don't change any files.
```

### Cursor

Use Know Your Code with your existing Cursor account and a model available on your plan. The skill adds instructions to Cursor's Agent; it requires no separate subscription, API key, or service. Cursor's normal [model usage and plan limits](https://cursor.com/docs/models-and-pricing) still apply.

For a local install, first clone this repository into a new directory:

```sh
git clone https://github.com/axis-ve/KYCode.git
```

From the directory containing that clone, copy the skills into your existing project. Replace `path/to/your-project` with its location:

```sh
mkdir -p "path/to/your-project/.cursor/skills"
cp -R KYCode/skills/* "path/to/your-project/.cursor/skills/"
```

For every local project, use this destination instead:

```sh
mkdir -p ~/.cursor/skills
cp -R KYCode/skills/* ~/.cursor/skills/
```

Alternatively, import the repository as a plugin in Cursor: open Customize, choose From GitHub Repository, enter the URL below, then install Know Your Code from the imported marketplace:

```text
https://github.com/axis-ve/KYCode
```

Open your project in Cursor, then send:

```text
/know-your-code What happens when I press Save?
Follow it from the button to storage. Don't change any files.
```

Replace "Save" with an action in your app. The host needs access to the project files.
Use the host's voice controls for the walkthrough. Expect a conversational explanation of the relevant code, with file references and a way to check what happens in companion text.

### Claude Code

Install the whole set as a plugin. This adds the skills, three slash commands, and two subagents:

```text
/plugin marketplace add axis-ve/KYCode
/plugin install know-your-code@know-your-code
```

For a local install without the plugin, clone the repository as above, then copy the skills into your project:

```sh
mkdir -p "path/to/your-project/.claude/skills"
cp -R KYCode/skills/* "path/to/your-project/.claude/skills/"
```

For every local project, use `~/.claude/skills/` as the destination instead.

Open your project in Claude Code and ask for what you want:

```text
What happens when I press Save?
Follow it from the button to storage. Don't change any files.
```

Claude reads the request and loads the skill that matches it. To choose one yourself, type its name. Claude Code prefixes plugin skills and commands with the plugin name, so with the plugin the main skill is `/know-your-code:know-your-code`. With a local copy it is `/know-your-code`.

The plugin also installs three commands, which run only when you type them:

- `/know-your-code:orient` maps an unfamiliar repository, and on a large one traces several entry points in parallel.
- `/know-your-code:why-broken` reproduces a symptom before naming a cause.
- `/know-your-code:explain-change` fetches a real diff before explaining it.

The commands use two subagents, which differ in how their limits hold. `code-path-tracer` has only read and search tools, so it cannot edit, create, or run anything. `check-runner` runs your project's own commands. It has no file-editing tools and its instructions forbid changing files through the shell, but its shell access means that limit rests on those instructions.

### Start a voice walkthrough in Cursor

In your project's Agent chat, select `/know-your-code`, then use Cursor's voice input to dictate the rest of your prompt. For example: "Walk me through what happens when I press Save. Keep it short, show me the files, and don't change anything." Continue with spoken follow-ups such as "Explain that function with less jargon."

Cursor documents [voice input in the Agents Window](https://cursor.com/changelog/3-1) as speech-to-text, with a press-and-hold `Ctrl+M` shortcut. Use the voice controls available in your installed version. Audio playback and interruption behavior depend on Cursor; this skill provides the code walkthrough instructions. Live voice verification is tracked in the [session acceptance checks](evals/session-checks.md).

## What it does

The skill gives the assistant instructions to work from your code and check its explanations against evidence:

- Talk through a user action in the relevant functions, requests, and stored data, with written evidence alongside the conversation.
- Follow interruptions and side questions, then resume the original walkthrough.
- Investigate a bug using source code, logs, and reproducible behavior.
- Make a requested change, verify it, and explain where to edit it next.
- Answer a focused question about code just traced, only when asked.

Exploration stays read-only unless you ask for changes. Say "less jargon," "go deeper," or "just fix it" to set the pace.

## The skills

`know-your-code` is the one to start with. The rest are companions, each written with a trigger the others should not match. Live routing checks are still pending; see [skill selection](evals/session-checks.md#skill-selection).

| Skill | For |
| --- | --- |
| [know-your-code](skills/know-your-code/SKILL.md) | Follow one action through your code, end to end. |
| [know-your-project](skills/know-your-project/SKILL.md) | Map an unfamiliar repository before you dive in. |
| [know-your-change](skills/know-your-change/SKILL.md) | Understand what a diff, commit, or pull request does. |
| [know-where-it-goes](skills/know-where-it-goes/SKILL.md) | Find where new code belongs, from the project's own precedents. |
| [know-what-you-want](skills/know-what-you-want/SKILL.md) | Turn a rough idea into a request that gets built right the first time. |
| [know-your-words](skills/know-your-words/SKILL.md) | Map the words you use to the identifiers the code uses. |
| [know-what-you-know](skills/know-what-you-know/SKILL.md) | Check your understanding, one question at a time. |
| [know-where-you-left-off](skills/know-where-you-left-off/SKILL.md) | Save and resume work across sessions, assistants, or people. |

The last three exist because most bad answers about a codebase are not reasoning failures. They are communication failures: you said "the login page" and the code says `AuthShell`, or you described an outcome and the assistant guessed at the behavior, or yesterday's verified finding is gone and nobody noticed.

## Try it on your project

In Codex, prefix prompts with `$know-your-code`. In Cursor, type `/know-your-code`. In Claude Code, ask in your own words, or pick the skill yourself with `/know-your-code:know-your-code` from the plugin or `/know-your-code` from a local copy.

Investigate a symptom:

```text
$know-your-code My edits disappear after a refresh.
Find the cause and show me how to reproduce it before proposing a fix.
```

Learn through a change:

```text
$know-your-code Add a confirmation before deleting a document.
Test it, then show me where I'd change the message.
```

Check your understanding:

```text
$know-your-code Ask me one question about the code we just explored.
Wait for my answer before explaining.
```

## Contribute

Read the [skill instructions](skills/know-your-code/SKILL.md), try the [behavioral evaluation cases](evals/README.md), or see [Contributing](CONTRIBUTING.md) to report a problem and run the repository checks.

## License

[MIT](LICENSE). Independent project, not affiliated with OpenAI, Cursor, or Anthropic.
