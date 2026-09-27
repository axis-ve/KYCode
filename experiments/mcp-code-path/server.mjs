import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { readFileSync } from "node:fs";
import { z } from "zod";

const templateUri = "ui://know-your-code/code-path/v1.html";
const widgetScript = readFileSync(new URL("./dist/widget.bundle.js", import.meta.url), "utf8");

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { color-scheme: light dark; font: 14px/1.45 system-ui, sans-serif; }
    body { margin: 0; padding: 16px; color: CanvasText; background: Canvas; }
    h1 { margin: 0 0 4px; font-size: 17px; }
    .summary { margin: 0 0 14px; opacity: .76; }
    ol { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
    li { display: grid; grid-template-columns: 26px 1fr; gap: 10px; align-items: start; }
    .number { display: grid; place-items: center; width: 24px; height: 24px; border: 1px solid color-mix(in srgb, CanvasText 24%, transparent); border-radius: 50%; font-size: 12px; }
    .step { min-width: 0; padding: 2px 0 10px; }
    .title { font-weight: 650; }
    .file { display: block; margin-top: 3px; overflow-wrap: anywhere; font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; opacity: .8; }
    .detail { margin: 5px 0 0; opacity: .8; }
    .check { margin-top: 14px; padding: 10px 12px; border-radius: 8px; background: color-mix(in srgb, CanvasText 7%, Canvas); }
    .check strong { display: block; margin-bottom: 3px; }
    .check code { overflow-wrap: anywhere; font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; }
    .empty { opacity: .7; }
  </style>
</head>
<body>
  <main aria-live="polite">
    <h1>Code path</h1>
    <p id="summary" class="summary">Waiting for a verified walkthrough…</p>
    <ol id="steps"></ol>
    <section id="check" class="check" hidden><strong>Try this check</strong><code id="check-command"></code></section>
  </main>
  <script>${widgetScript}</script>
</body>
</html>`;

const server = new McpServer({ name: "know-your-code-code-path-spike", version: "0.1.0" });

server.registerResource("code-path-card", templateUri, {}, async () => ({
  contents: [{
    uri: templateUri,
    mimeType: "text/html;profile=mcp-app",
    text: html,
    _meta: { ui: { prefersBorder: true } },
  }],
}));

server.registerTool(
  "render_code_path",
  {
    title: "Show a code path",
    description: "Use only after inspecting the repository for a useful linear walkthrough with at least three source-verified steps from user action to effect. Pass evidence-grounded steps, file paths, and an optional local check. This tool only renders the supplied data; it does not inspect or change files.",
    inputSchema: {
      summary: z.string().max(180),
      steps: z.array(z.object({
        title: z.string().min(1).max(100),
        file: z.string().max(300).optional(),
        line: z.number().int().positive().optional(),
        detail: z.string().max(300).optional(),
      })).min(3).max(8),
      check: z.string().max(240).optional(),
    },
    outputSchema: {
      summary: z.string(),
      steps: z.array(z.object({
        title: z.string(),
        file: z.string().optional(),
        line: z.number().int().positive().optional(),
        detail: z.string().optional(),
      })),
      check: z.string().optional(),
    },
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    _meta: { ui: { resourceUri: templateUri } },
  },
  async (data) => ({
    structuredContent: data,
    content: [{
      type: "text",
      text: [
        `Code path: ${data.summary}`,
        ...data.steps.map((step, index) => {
          const location = step.file ? ` (${step.file}${step.line ? `:${step.line}` : ""})` : "";
          return `${index + 1}. ${step.title}${location}${step.detail ? ` — ${step.detail}` : ""}`;
        }),
        ...(data.check ? [`Check: ${data.check}`] : []),
      ].join("\n"),
    }],
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
