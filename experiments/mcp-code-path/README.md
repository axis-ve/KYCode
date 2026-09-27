# Optional MCP code path card for Codex

This local MCP Apps server is an optional transcript companion for the [Know Your Code skill](../../skills/know-your-code/SKILL.md). The skill calls `render_code_path` only after tracing a useful multi-hop path through source. The server receives the verified path and renders it; it does not scan the repository, write files, call external services, or send data outside the local MCP process.

The card shows a summary, three to eight ordered steps with optional file/line and detail, and an optional local check command. The MCP tool returns those details as readable plain text and `structuredContent` when a host does not render the UI. The skill also keeps its source-linked written path and check in the transcript.

## Requirements

- Node.js 18 or newer
- npm access to install the project-local dependencies

## Run the local protocol check

```sh
cd experiments/mcp-code-path
npm ci
npm run check
```

The check builds the widget, starts the server over local stdio, inspects the advertised tool, calls it with sample data, and reads the registered MCP Apps resource. It verifies that the bundled MCP Apps client includes the initialization lifecycle and tool-result handler. It does not connect that client to a real host or test iframe rendering.

## Connect to Codex locally

After running the local protocol check above, return to the repository root and register the local stdio server in your own Codex configuration:

```sh
codex mcp add know-your-code-path -- node "$(pwd)/experiments/mcp-code-path/server.mjs"
codex mcp list
```

The server loads its built widget relative to `server.mjs`, so the current working directory does not matter. Restart the Codex session to pick up the MCP connection. To remove this optional local setup, run `codex mcp remove know-your-code-path`. This is a local developer setup; the installable skill does not depend on the server.

Open a project with the skill installed and ask for a multi-hop action, such as “Follow Save from the button to storage.” Check that the assistant reads the source first, calls `render_code_path` only with verified steps and locations, and still writes a readable path with source references and a check. Repeat with the server unavailable and with a short or uncertain trace; those should use the ordinary text answer without a tool call. Record tool discovery/call, plain-text output, and any visible card as separate observations.

## What this does and does not establish

The implementation follows OpenAI's documented MCP Apps resource MIME type (`text/html;profile=mcp-app`), `_meta.ui.resourceUri`, and `ui/notifications/tool-result` pattern. It bundles the `@modelcontextprotocol/ext-apps` `App` client and `PostMessageTransport`; this client performs the `ui/initialize` / `ui/notifications/initialized` handshake, then dispatches the tool result to the card. The MCP Apps specification requires this lifecycle before the host sends notifications. The local check confirms the helper bundle is present but does not exercise an iframe host.

An earlier Codex CLI integration check used `codex exec --ephemeral` with a temporary MCP configuration: Codex discovered and called `render_code_path`. That result and this protocol check do not establish that Codex desktop renders the card in its transcript. Desktop rendering remains untested until a real host session observes it.

## Known limits

- The card's file references are text, not host-aware clickable source links.
- The server reads its bundled widget from disk, does not inspect the user's repository, and relies on the model to pass verified steps.
- The bundled MCP Apps client implements initialization, but it has not been exercised against a real iframe host in this spike.
- The widget is intentionally static: no widget-initiated tools, persistence, remote assets, or UI-to-model context updates.
- A compatible host may choose not to render MCP Apps UI; the tool's plain-text response is the fallback.

## OpenAI documentation used

- [Add UI to your MCP server](https://developers.openai.com/plugins/build/chatgpt-ui)
- [Build an MCP server](https://developers.openai.com/plugins/build/mcp-server)
- [Troubleshooting](https://developers.openai.com/plugins/deploy/troubleshooting)
- [MCP Apps lifecycle and UI bridge](https://github.com/modelcontextprotocol/ext-apps/blob/main/docs/overview.md)
