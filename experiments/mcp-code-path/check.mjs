import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({ command: process.execPath, args: ["server.mjs"] });
const client = new Client({ name: "know-your-code-code-path-check", version: "0.1.0" });

try {
  await client.connect(transport);
  const { tools } = await client.listTools();
  const tool = tools.find((candidate) => candidate.name === "render_code_path");
  assert.ok(tool, "render_code_path is advertised");
  assert.equal(tool.annotations?.readOnlyHint, true);
  assert.equal(tool._meta?.ui?.resourceUri, "ui://know-your-code/code-path/v1.html");
  assert.equal(tool.inputSchema.properties.steps.minItems, 3);

  const sample = {
    summary: "A user action reaches the save handler",
    steps: [
      { title: "Click Save", file: "src/Editor.tsx", line: 42 },
      { title: "Validate draft", file: "src/save.ts", line: 18, detail: "The handler checks the draft." },
      { title: "Persist note", file: "src/store.ts", line: 27, detail: "The store writes the validated note." },
    ],
    check: "npm test -- --runInBand save",
  };
  const result = await client.callTool({ name: "render_code_path", arguments: sample });
  assert.deepEqual(result.structuredContent, sample);
  assert.match(result.content[0].text, /Code path: A user action reaches the save handler/);
  assert.match(result.content[0].text, /1\. Click Save \(src\/Editor\.tsx:42\)/);
  assert.match(result.content[0].text, /2\. Validate draft \(src\/save\.ts:18\) — The handler checks the draft\./);
  assert.match(result.content[0].text, /3\. Persist note \(src\/store\.ts:27\) — The store writes the validated note\./);
  assert.match(result.content[0].text, /Check: npm test -- --runInBand save/);

  const { contents } = await client.readResource({ uri: "ui://know-your-code/code-path/v1.html" });
  assert.equal(contents[0].mimeType, "text/html;profile=mcp-app");
  assert.match(contents[0].text, /ui\/initialize/);
  assert.match(contents[0].text, /ui\/notifications\/initialized/);
  assert.match(contents[0].text, /ui\/notifications\/tool-result/);
  assert.doesNotMatch(contents[0].text, /<script\s+src=/i);
  const widgetSource = readFileSync(new URL("./widget.js", import.meta.url), "utf8");
  assert.match(widgetSource, /new PostMessageTransport\(window\.parent, window\.parent\)/);
  assert.match(widgetSource, /app\.connect\(/);
  assert.match(widgetSource, /title\.textContent = step\.title/);
  console.log("MCP protocol check passed: read-only tool, result, inline widget bundle, and MCP Apps initialization client are wired.");
} finally {
  await client.close();
}
