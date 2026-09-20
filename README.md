# Know Your Code

You vibe coded it. Now understand what you shipped.

Know Your Code is a Codex skill that helps you follow your project's code, investigate bugs, and make changes you can explain afterward. It works from your actual files and logs.

## Install in Codex

Paste this into a Codex task:

```text
$skill-installer Install the skill from https://github.com/axis-ve/KYCode/tree/main/skills/know-your-code
```

Then open the project you want to understand and send:

```text
$know-your-code Help me understand this project. Start with what happens when a user opens it.
```

If the skill does not appear, restart Codex and try again. You need Codex with access to your project's files. The skill itself needs no API key, server, or npm install. Installation uses Codex's bundled skill installer. See the [official skill documentation](https://developers.openai.com/codex/skills/).

### Install for one project instead

1. [Download this repository](https://github.com/axis-ve/KYCode/archive/refs/heads/main.zip) and unzip it.
2. In your own project's root, create `.agents/skills/` if it does not exist.
3. Copy the entire `skills/know-your-code` folder from the download into that directory.
4. Open your project in Codex and invoke `$know-your-code` as shown above.

The installed entry point must be at:

```text
your-project/.agents/skills/know-your-code/SKILL.md
```

Copy the whole folder, including its license and UI metadata. Cloning KYCode alone does not install it in your project.

### Update or uninstall

For a manual install, back up any local edits and replace the installed `know-your-code` folder with the latest copy. To uninstall, remove that folder.

If you used `$skill-installer`, ask Codex to locate the installed copy and update or remove it. The installer may refuse to overwrite an existing skill. Preserve your local edits before replacing it.

## Try it

```text
$know-your-code What happens when I press Save? Follow it from the button to storage. Don't change anything yet.
```

```text
$know-your-code My edits disappear after a refresh. Find out why before proposing a fix.
```

```text
$know-your-code Add a confirmation before deleting a document. Test it, then show me where I'd change the message.
```

Ask for less jargon, a shorter answer, or a deeper explanation as you go. Questions stay read-only. A request to implement a change authorizes that work within the scope you give.

If your Codex app supports voice, you can talk through the same work. The skill does not supply voice controls or microphone access. Start voice using your app's own control after invoking the skill. Live voice behavior has not been validated by this repository.

## What's in this repo

- [Skill instructions](skills/know-your-code/SKILL.md): what Codex reads when you invoke the skill.
- [Evaluation guide](evals/README.md): reproducible fixture setup, review criteria, and testing limits.
- [Contributing](CONTRIBUTING.md): run checks and report a failure.

This repository contains one self-contained skill. It does not require another skill pack or a custom application.

## License

[MIT](LICENSE). The installable skill also includes a copy of the license. Know Your Code is an independent project and is not an official OpenAI product.
