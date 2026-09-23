# MCP code path card spike

Small, isolated MCP Apps prototype for a Know Your Code walkthrough card. It receives a short, evidence-grounded path from the caller and renders it. It does not scan the repository, write files, call external services, or send data outside the local MCP process.

The card shows a summary, up to eight ordered steps with optional file/line and detail, and an optional local check command. The MCP tool returns the same information as plain text and `structuredContent` when a host does not render the UI.

## Requirements

- Node.js 18 or newer
- npm access to install the project-local dependencies

## Run the local protocol check

```sh
cd experiments/mcp-code-path
npm install
npm run check
```

The check builds the widget, starts the server over local stdio, inspects the advertised tool, calls it with sample data, and reads the registered MCP Apps resource. It verifies that the bundled MCP Apps client includes the initialization lifecycle and tool-result handler. It does not connect that client to a real host or test iframe rendering.

## Connect to a host

This server uses stdio. First run `npm run build`, then in a temporary MCP client configuration launch `node` with the absolute path to `server.mjs` as its argument and set this directory as the working directory. For Codex, this is only a manual test configuration; don't copy it into shared project configuration without review. Restart the MCP connection after changes.

Then ask the host to render a code path using only repository facts it has already verified. Try a 3–5 step flow and confirm the plain-text fallback remains understandable.

## What this does and does not establish

The implementation follows OpenAI's documented MCP Apps resource MIME type (`text/html;profile=mcp-app`), `_meta.ui.resourceUri`, and `ui/notifications/tool-result` pattern. It bundles the `@modelcontextprotocol/ext-apps` `App` client and `PostMessageTransport`; this client performs the `ui/initialize` / `ui/notifications/initialized` handshake, then dispatches the tool result to the card. The MCP Apps specification requires this lifecycle before the host sends notifications. The local check confirms the helper bundle is present but does not exercise an iframe host.

Codex CLI integration was checked with `codex exec --ephemeral` using a temporary MCP configuration: Codex discovered and called `render_code_path`. OpenAI's current UI guide explicitly describes iframe rendering in ChatGPT. Its troubleshooting guide says server/tool checks apply to ChatGPT and Codex, while UI behavior described there is ChatGPT behavior. The CLI check does not establish that Codex desktop renders the card in its transcript; desktop rendering remains untested.

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
