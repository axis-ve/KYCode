import { App, PostMessageTransport } from "@modelcontextprotocol/ext-apps";

const summary = document.querySelector("#summary");
const steps = document.querySelector("#steps");
const check = document.querySelector("#check");
const command = document.querySelector("#check-command");

function render(data) {
  if (!data || !Array.isArray(data.steps)) return;
  summary.textContent = data.summary || "Verified code path";
  steps.replaceChildren();
  data.steps.forEach((step, index) => {
    const row = document.createElement("li");
    const number = document.createElement("span");
    number.className = "number";
    number.textContent = String(index + 1);
    const content = document.createElement("div");
    content.className = "step";
    const title = document.createElement("div");
    title.className = "title";
    title.textContent = step.title;
    content.append(title);
    if (step.file) {
      const file = document.createElement("code");
      file.className = "file";
      file.textContent = step.file + (step.line ? ":" + step.line : "");
      content.append(file);
    }
    if (step.detail) {
      const detail = document.createElement("p");
      detail.className = "detail";
      detail.textContent = step.detail;
      content.append(detail);
    }
    row.append(number, content);
    steps.append(row);
  });
  if (data.check) {
    command.textContent = data.check;
    check.hidden = false;
  } else {
    check.hidden = true;
  }
}

const app = new App({ name: "Know Your Code path card", version: "0.1.0" }, {});
app.addEventListener("toolresult", (params) => render(params.structuredContent));
app.connect(new PostMessageTransport(window.parent, window.parent)).catch((error) => {
  summary.textContent = "Could not initialize the MCP Apps host connection.";
  console.error("MCP Apps initialization failed", error);
});
