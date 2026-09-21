![Know Your Code. Your code. Your aha. A skill for Codex and Cursor.](assets/cover.png)

<h1 align="center">Know Your Code</h1>

A skill for understanding how your app works, finding why it breaks, and making changes you can maintain. It works in Codex and Cursor from the same instructions.

## Install

### Codex

Send this in Codex:

```text
$skill-installer Install https://github.com/axis-ve/KYCode/tree/main/skills/know-your-code
```

Open your project in Codex, then send:

```text
$know-your-code What happens when I press Save?
Follow it from the button to storage. Don't change any files.
```

### Cursor

Copy the skill into the project you want to understand:

```sh
mkdir -p .cursor/skills
cp -r skills/know-your-code .cursor/skills/
```

For every local project, copy it to `~/.cursor/skills/know-your-code/` instead. To import the GitHub repository as a Cursor plugin, open Customize and choose From GitHub Repository:

```text
https://github.com/axis-ve/KYCode
```

Open your project in Cursor, then send:

```text
/know-your-code What happens when I press Save?
Follow it from the button to storage. Don't change any files.
```

Replace "Save" with an action in your app. The host needs access to the project files.
Expect a walkthrough of the relevant code, with file references and a way to check what happens.

## What it does

The skill gives the assistant instructions to work from your code and check its explanations against evidence:

- Trace a user action through the relevant functions, requests, and stored data.
- Investigate a bug using source code, logs, and reproducible behavior.
- Make a requested change, verify it, and explain where to edit it next.
- Help you test your understanding with questions about code you have just explored.

Exploration stays read-only unless you ask for changes. Say "less jargon," "go deeper," or "just fix it" to set the pace.

## Try it on your project

In Codex, prefix prompts with `$know-your-code`. In Cursor, type `/know-your-code`.

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

[MIT](LICENSE). Independent project, not affiliated with OpenAI or Cursor.
