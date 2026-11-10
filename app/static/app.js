"use strict";
const $ = id => document.getElementById(id);
const state = { history: [], trace: null, quiz: null, quizCorrect: false, sessionId: null, recorder: null, chunks: [], audioBlob: null, episodes: [], creators: [] };
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = cents => cents ? "$" + (cents / 100).toFixed(2).replace(/\.00$/, "") : "Free";
const dollars = cents => "$" + ((cents || 0) / 100).toFixed(2);

function byokHeaders() {
  const h = { "Content-Type": "application/json" };
  if ($("provider").value && $("apiKey").value.trim()) {
    h["X-Provider"] = $("provider").value; h["X-Api-Key"] = $("apiKey").value.trim();
    if ($("model").value.trim()) h["X-Model"] = $("model").value.trim();
  }
  return h;
}
async function api(path, options = {}) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || ("HTTP " + res.status));
  return data;
}
const post = (path, body, headers) => api(path, { method: "POST", headers: headers || { "Content-Type": "application/json" }, body: JSON.stringify(body) });
function copied(btn) { const old = btn.textContent; btn.textContent = "Copied"; setTimeout(() => btn.textContent = old, 1400); }
function banner(text, good) { const b = $("banner"); $("bannerText").textContent = text; b.className = "alert " + (good ? "alert-success" : "alert-warning"); }
function project() { return $("projectPath").value.trim(); }
function handle() { return $("handle").value.trim().toLowerCase() || "demo"; }

// ---------- views ----------
function show(view) {
  document.querySelectorAll(".view").forEach(v => v.classList.add("hidden"));
  $("view-" + view).classList.remove("hidden");
  document.querySelectorAll(".side-item[data-view]").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  $("crumb").textContent = { studio: "Studio", discover: "Discover", episode: "Episode", revenue: "Revenue" }[view] || view;
  document.title = $("crumb").textContent + " — KYCode Studio";
  document.querySelectorAll(".side-item[data-view]").forEach(b => b.toggleAttribute("aria-current", b.dataset.view === view));
  const heading = $("view-" + view).querySelector("h1"); if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
  if (location.pathname === "/") history.replaceState({}, "", (view === "studio" ? "/" : "/#" + view) + location.search);
  if (view === "discover") loadDiscover();
  if (view === "revenue") loadRevenue();
}
document.querySelectorAll(".side-item[data-view]").forEach(b => b.onclick = () => show(b.dataset.view));
$("backBtn").onclick = () => show("discover");
$("handle").oninput = () => { $("who").textContent = handle(); $("avatarInit").textContent = (handle()[0] || "K").toUpperCase(); };
$("cname").oninput = () => { if ($("cname").value.trim()) $("whoName").textContent = $("cname").value.trim(); };

// ---------- settings persist (browser only) ----------
localStorage.removeItem("kyc:apiKey");  // keys are session-only now
["provider", "model", "handle", "projectPath"].forEach(id => {
  const saved = localStorage.getItem("kyc:" + id); if (saved) $(id).value = saved;
  $(id).addEventListener("change", () => localStorage.setItem("kyc:" + id, $(id).value));
});
$("apiKey").value = sessionStorage.getItem("kyc:apiKey") || "";
$("apiKey").addEventListener("change", () => sessionStorage.setItem("kyc:apiKey", $("apiKey").value));
$("who").textContent = handle();

// ---------- scan ----------
$("scanBtn").onclick = async () => {
  $("scanBtn").disabled = true; $("scanOut").textContent = "Scanning (read-only)…";
  try {
    const s = await post("/api/project/scan", { path: project() });
    state.scanned = true; setSteps();
    const langs = Object.entries(s.languages).map(([k, v]) => `${k} ${v}`).join(" · ");
    const labels = s.entry_labels.map(e => `"${e.label}"`).join(", ") || "no labelled actions found";
    $("scanOut").innerHTML = `${s.file_count} source files (${esc(s.size_class)} project) — ${esc(langs)}.<br>Actions found: ${esc(labels)}.<br>Try: “What happens when I press Save?”`;
  } catch (e) { $("scanOut").textContent = "Scan failed: " + e.message; } finally { $("scanBtn").disabled = false; }
};

// ---------- voice ----------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
if (!SR) $("voiceNote").textContent = "Speech input is not available in this browser — typing works fully. Try Chrome for the mic.";
else if (!("speechSynthesis" in window)) $("voiceNote").textContent = "Spoken replies are not available in this browser — replies will be text.";
function speak(text) {
  if (!$("speakToggle").checked || !("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.slice(0, 900)); u.rate = 1.02; speechSynthesis.speak(u);
}
$("micBtn").onclick = () => {
  if (!SR) { banner("Speech input unavailable in this browser. Type instead — everything else works."); return; }
  if (recognition) { recognition.stop(); return; }
  if ("speechSynthesis" in window) speechSynthesis.cancel(); // interrupt, keep resume point
  recognition = new SR(); recognition.lang = "en-US"; recognition.interimResults = false;
  recognition.onresult = ev => { $("chatInput").value = ev.results[0][0].transcript; sendChat("walkthrough"); };
  recognition.onend = () => { recognition = null; $("micBtn").classList.remove("on"); };
  recognition.onerror = ev => banner("Mic error: " + ev.error + ". Typing still works.");
  recognition.start(); $("micBtn").classList.add("on"); 
};

// ---------- chat ----------
function addTurn(role, content, source) {
  const div = document.createElement("div"); div.className = "msg " + role;
  const initials = role === "user" ? (handle()[0] || "Y").toUpperCase() : "KY";
  div.innerHTML = `<span class="avatar">${esc(initials)}</span><div class="body">` +
    `<div class="meta"><b>${role === "user" ? "You" : "KYCode agent"}</b>${source ? `<span class="badge badge-outline">${esc(source)}</span>` : ""}</div>` +
    `<div class="bubble">${esc(content)}</div></div>`;
  $("transcript").appendChild(div); $("transcript").scrollTop = $("transcript").scrollHeight;
  state.history.push({ role, content });
}
function setSteps() {
  const done = { "step-scan": !!state.scanned, "step-talk": state.history.some(t => t.role === "user"), "step-quiz": state.quizCorrect, "step-pub": !!state.published };
  Object.entries(done).forEach(([id, ok]) => { const el = $(id); if (el) { el.classList.toggle("done", ok); el.classList.remove("now"); } });
  const next = ["step-scan", "step-talk", "step-quiz", "step-pub"].find(id => !done[id]);
  document.querySelectorAll(".step[id]").forEach(el => el.removeAttribute("aria-current")); if (next) { $(next).classList.add("now"); $(next).setAttribute("aria-current", "step"); }
}
function renderEvidence(trace) {
  if (!trace) return; state.trace = trace;
  $("codePathEmpty").style.display = trace.hops.length ? "none" : "";
  $("codePath").innerHTML = trace.hops.map(h =>
    `<li><span class="t-dot"></span><div class="t-title">${esc(h.label)}<span class="file-ref">${esc(h.file)}:${h.line}</span></div><div class="code-block">${esc(h.snippet)}</div></li>`).join("");
  $("storedData").innerHTML = trace.stored_data.length
    ? trace.stored_data.map(x => `<li><span class="file-ref">${esc(x.file)}</span><span>${esc(x.detail)}</span></li>`).join("") : "<li class='muted'>No write found on this path.</li>";
  $("reach").innerHTML = trace.also_reached_by.length
    ? trace.also_reached_by.map(r => `<li><strong>${esc(r.function)}()</strong><span class="muted">${r.count} call site${r.count === 1 ? "" : "s"}${r.call_sites.length ? " · " + esc(r.call_sites.join(", ")) : ""}</span></li>`).join("")
    : "<li class='muted'>None traced yet.</li>";
  $("checks").innerHTML = trace.checks.map(c =>
    `<div class="check-row"><div class="code-block">${esc(c.command)}</div><button class="btn btn-outline btn-sm" data-copy="${esc(c.command)}">Copy</button></div><p class="text-xs muted" style="margin-top:.25rem">${esc(c.label)} · suggested, not run by the Studio</p>`).join("");
  document.querySelectorAll("[data-copy]").forEach(b => b.onclick = () => { navigator.clipboard.writeText(b.dataset.copy); copied(b); });
  $("proofBadge").innerHTML = trace.hops.length
    ? `<span class="badge badge-success">Verified from source</span><span class="badge">${trace.hops.length} hops</span>` +
      (state.quizCorrect ? `<span class="badge badge-info">Quiz passed</span>` : `<span class="badge badge-outline">Quiz pending</span>`)
    : `<span class="badge badge-outline">No trace yet</span><span class="text-xs muted">Ask about a real action in your app.</span>`;
  setSteps();
}
async function sendChat(mode, preset) {
  const text = (preset ?? $("chatInput").value).trim(); if (!text) return;
  $("chatInput").value = "";
  const isQuizAnswer = state.quiz && mode === "walkthrough";
  $("sendBtn").disabled = true; $("micBtn").disabled = true; $("transcript").setAttribute("aria-busy", "true");
  addTurn("user", text);
  $("resume").textContent = "tracing your real code…";
  try {
    const data = await post("/api/chat", {
      path: project(), message: text, history: state.history.slice(-8),
      mode: isQuizAnswer ? "quiz-answer" : mode, session_id: state.sessionId || undefined
    }, byokHeaders());
    if (data.session_id) state.sessionId = data.session_id;
    if (data.quiz) state.quiz = data.quiz;
    if (data.quiz_result) { state.quizCorrect = !!data.quiz_result.correct; if (data.quiz_result.correct) state.quiz = null; }
    addTurn("assistant", data.reply, data.source + (data.provider_error ? " (provider error: " + data.provider_error + ")" : ""));
    renderEvidence(data.trace);
    $("resume").textContent = data.resume_point || "ready";
    speak(data.reply);
  } catch (e) { addTurn("assistant", "Something failed: " + e.message + ". Nothing was changed."); $("resume").textContent = "ready"; }
  finally { $("sendBtn").disabled = false; $("micBtn").disabled = false; $("transcript").removeAttribute("aria-busy"); saveDraft(); }
}
$("sendBtn").onclick = () => sendChat("walkthrough");
$("chatInput").addEventListener("keydown", e => { if (e.key === "Enter") sendChat("walkthrough"); });
document.querySelectorAll("[data-chip]").forEach(b => b.onclick = () => {
  const chip = b.dataset.chip;
  if (chip === "walk") sendChat("walkthrough", "What happens when I press Save? Follow it from the button to storage. Don't change any files.");
  else if (chip === "diagnose") sendChat("diagnose", "Something is broken around Save. Reproduce it along the real path before naming a cause.");
  else if (chip === "quiz") sendChat("quiz", "Quiz me on the Save path. One question, wait for my answer.");
  else if (chip === "cohost") sendChat("cohost", "Co-host an episode with me: what happens when I press Save in my app?");
  else if (chip === "jargon") sendChat("walkthrough", "Explain that again with less jargon, same facts.");
  else if (chip === "deeper") sendChat("walkthrough", "Go deeper on the last step. What else calls it, and what would break if it changed?");
});

// ---------- recording ----------
$("recBtn").onclick = async () => {
  if (state.recorder) { state.recorder.stop(); return; }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    banner("Audio recording is not available in this browser. You can still publish the transcript episode with narration playback.");
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.chunks = []; state.recorder = new MediaRecorder(stream);
    state.recorder.ondataavailable = e => e.data.size && state.chunks.push(e.data);
    state.recorder.onstop = () => {
      state.audioBlob = new Blob(state.chunks, { type: state.recorder.mimeType || "audio/webm" });
      stream.getTracks().forEach(t => t.stop()); state.recorder = null;
      $("recBtn").className = "btn btn-outline btn-sm"; $("recBtn").textContent = "Record episode"; $("recDot").style.display = "none";
      $("recState").textContent = `Recorded ${(state.audioBlob.size / 1024).toFixed(0)} KB of your voice. It uploads when you publish.`;
    };
    state.recorder.start(); $("recBtn").className = "btn btn-destructive btn-sm"; $("recBtn").textContent = "Stop recording"; $("recDot").style.display = "block";
    $("recState").textContent = "Recording your mic… talk with your codebase, then stop and publish.";
  } catch (e) { banner("Mic recording failed: " + e.message); }
};

// ---------- creator + publish ----------
async function saveCreator() {
  const data = await post("/api/creators", {
    handle: handle(), name: $("cname").value.trim() || handle(), bio: $("bio").value.trim(),
    project_name: $("projectName").value.trim(), project_url: $("projectUrl").value.trim(),
    tip_cents: Math.round(parseFloat($("tipPrice").value || "5") * 100),
    sub_cents: Math.round(parseFloat($("subPrice").value || "9") * 100),
    stripe_account_id: $("stripeAccount").value.trim()
  });
  return data.creator;
}
$("saveCreatorBtn").onclick = async () => { try { await saveCreator(); banner("Creator saved. Your episode pages now link your project.", true); loadRevenue(); } catch (e) { banner(e.message); } };

$("publishBtn").onclick = async () => {
  if (!state.history.some(t => t.role === "user")) { banner("Talk with your codebase first — an episode needs your voice in it."); return; }
  $("publishBtn").disabled = true;
  try {
    await saveCreator();
    const trace = state.trace || { hops: [], checks: [] };
    const data = await post("/api/episodes", {
      creator: handle(), title: $("epTitle").value.trim() || "Talking with my codebase",
      summary: $("epSummary").value.trim(), action: trace.action || "",
      transcript: state.history, session_id: state.sessionId || undefined,
      price_cents: Math.round(parseFloat($("epPrice").value || "0") * 100), published: true
    });
    const ep = data.episode;
    if (state.audioBlob) {
      await fetch(`/api/episodes/${ep.id}/audio`, { method: "POST", headers: { "Content-Type": state.audioBlob.type || "audio/webm" }, body: state.audioBlob });
      state.audioBlob = null;
    }
    const base = location.origin;
    $("publishOut").innerHTML =
      `<hr class="separator"><p class="text-sm"><strong>Live.</strong> Share it everywhere — the proof travels with it.</p>
       <div class="share-row"><input class="input" readonly value="${base}/e/${ep.id}"><button class="btn btn-outline btn-sm" id="copyLinkBtn">Copy link</button></div>
       <div class="share-row"><input class="input" readonly value="${base}/rss/${handle()}.xml"><button class="btn btn-outline btn-sm" id="copyRssBtn">Copy RSS</button></div>
       <div class="share-row"><input class="input" readonly value="Embed player for your site"><button class="btn btn-outline btn-sm" id="copyEmbedBtn">Copy embed</button></div>`;
    state.published = true; setSteps();
    $("copyLinkBtn").onclick = () => navigator.clipboard.writeText(`${base}/e/${ep.id}`);
    $("copyRssBtn").onclick = () => navigator.clipboard.writeText(`${base}/rss/${handle()}.xml`);
    $("copyEmbedBtn").onclick = () => navigator.clipboard.writeText(`<iframe src="${base}/embed/${ep.id}" width="100%" height="220" frameborder="0"></iframe>`);

    banner("Episode published: " + ep.title, true);
  } catch (e) { banner("Publish failed: " + e.message); } finally { $("publishBtn").disabled = false; }
};

// ---------- payments ----------
async function checkout(kind, creator, episodeId) {
  try {
    const data = await post("/api/stripe/checkout", { kind, creator, episode_id: episodeId });
    if (!data.configured) { banner(data.message + " (Revenue tab explains setup.)"); return; }
    if (data.error) { banner(data.error); return; }
    location.href = data.url;
  } catch (e) { banner("Checkout failed: " + e.message); }
}
async function checkStripeReturn() {
  const q = new URLSearchParams(location.search);
  if (q.get("paid") === "1" && q.get("session_id")) {
    const data = await api("/api/stripe/verify?session_id=" + encodeURIComponent(q.get("session_id"))).catch(() => ({}));
    banner(data.verified ? `Payment confirmed by Stripe (${money(data.amount_cents)}). Thank you for backing a builder who learns in public.` : "Payment not confirmed yet — no charge was recorded here.", !!data.verified);
    history.replaceState({}, "", location.pathname);
  } else if (q.get("paid") === "0") { banner("Checkout cancelled. Nothing was charged."); history.replaceState({}, "", location.pathname); }
}

// ---------- discover + episode ----------
function episodeCard(ep) {
  const proof = ep.proof?.verified ? `<span class="badge badge-success">Verified · ${ep.proof.hops} hops</span>${ep.proof.quiz_correct ? `<span class="badge badge-info">Quiz passed</span>` : ""}` : `<span class="badge badge-outline">No proof attached</span>`;
  return `<a class="ep-card frame" href="/e/${ep.id}" data-ep="${ep.id}"><div class="frame-panel">
    <div class="row" style="margin-bottom:.5rem"><span class="avatar" style="width:1.75rem;height:1.75rem;font-size:.6875rem">${esc((ep.creator[0] || "K").toUpperCase())}</span><span class="text-sm" style="font-weight:600">@${esc(ep.creator)}</span>${ep.demo ? `<span class="badge badge-warning">Demo</span>` : ""}<span style="flex:1"></span><span class="badge ${ep.price_cents ? "badge-invert" : "badge-outline"}">${money(ep.price_cents)}</span></div>
    <h3>${esc(ep.title)}</h3><p class="text-sm muted" style="margin-top:.375rem">${esc(ep.summary)}</p>
    <div class="ep-meta">${proof}${ep.audio_path ? `<span class="badge">Recorded audio</span>` : `<span class="badge badge-outline">Narration</span>`}</div>
  </div></a>`;
}
async function loadDiscover() {
  if (!state.episodes.length) $("episodeGrid").innerHTML = "<div class=\"skeleton\"></div><div class=\"skeleton\"></div><div class=\"skeleton\"></div>";
  const [eps, crs] = await Promise.all([api("/api/episodes"), api("/api/creators")]);
  state.episodes = eps.episodes; state.creators = crs.creators;
  renderDiscover($("search").value || "");
}
function renderDiscover(term) {
  const t = term.toLowerCase();
  const list = state.episodes.filter(e => !t || (e.title + e.summary + e.creator + e.action).toLowerCase().includes(t));
  const verified = state.episodes.filter(e => e.proof?.verified).length;
  const hops = state.episodes.reduce((n, e) => n + (e.proof?.hops || 0), 0);
  $("statsRow").innerHTML = [
    [state.episodes.length, "Episodes published"], [verified, "With verified proof"],
    [hops, "Source hops checked"], [state.creators.length, "Creators"]
  ].map(([n, l]) => `<div class="frame"><div class="frame-panel stat"><div class="num">${n}</div><div class="lab">${l}</div></div></div>`).join("");
  $("discoverCount").textContent = list.length + " shown";
  $("episodeGrid").innerHTML = list.length ? list.map(episodeCard).join("") : `<div class="empty" style="grid-column:1/-1">No episodes match. Be the first — record one in the Studio.</div>`;
  document.querySelectorAll("[data-ep]").forEach(card => card.onclick = e => { e.preventDefault(); openEpisode(+card.dataset.ep); });
  $("creatorGrid").innerHTML = state.creators.map(c =>
    `<article class="frame creator-card"><div class="frame-panel">
     <div class="head"><span class="avatar">${esc((c.handle[0] || "K").toUpperCase())}</span><span><span style="font-weight:600;display:block;line-height:1.2">${esc(c.name)}</span><span class="text-xs muted">@${esc(c.handle)}</span></span></div>
     <p class="text-sm muted">${esc(c.bio || "Learning their codebase in public.")}</p>
     ${c.project_url ? `<p class="text-sm" style="margin-top:.375rem">Building <a href="${esc(c.project_url)}" target="_blank" rel="noopener">${esc(c.project_name || "their project")}</a></p>` : ""}
     <div class="actions"><button class="btn btn-outline btn-sm" data-tip="${esc(c.handle)}">Tip ${money(c.tip_cents)}</button><button class="btn btn-primary btn-sm" data-sub="${esc(c.handle)}">Subscribe ${money(c.sub_cents)}/mo</button><a class="btn btn-ghost btn-sm" href="/rss/${esc(c.handle)}.xml">RSS</a></div>
    </div></article>`).join("");
  document.querySelectorAll("[data-tip]").forEach(b => b.onclick = e => { e.stopPropagation(); checkout("tip", b.dataset.tip); });
  document.querySelectorAll("[data-sub]").forEach(b => b.onclick = e => { e.stopPropagation(); checkout("sub", b.dataset.sub); });
}
$("search").oninput = () => renderDiscover($("search").value);

async function openEpisode(id) {
  const { episode: ep } = await api("/api/episodes/" + id);
  const creator = state.creators.find(c => c.handle === ep.creator) || {};
  const hops = ep.code_path.map(h => `<li><span class="t-dot"></span><div class="t-title">${esc(h.label)}<span class="file-ref">${esc(h.file)}:${h.line}</span></div><div class="code-block">${esc(h.snippet)}</div></li>`).join("");
  const turns = ep.transcript.map(t => `<div class="msg ${esc(t.role)}"><span class="avatar">${t.role === "user" ? esc((ep.creator[0] || "C").toUpperCase()) : "KY"}</span><div class="body"><div class="meta"><b>${t.role === "user" ? "Creator" : "Agent"}</b></div><div class="bubble">${esc(t.content)}</div></div></div>`).join("");
  $("episodeDetail").innerHTML = `
  <div class="episode-hero">
    <div class="frame"><div class="frame-header">Episode<span class="spacer"></span>${ep.demo ? `<span class="badge badge-warning">Demo — real fixture trace</span>` : ""}</div>
    <div class="frame-panel">
      <h1>${esc(ep.title)}</h1>
      <p class="muted text-sm" style="margin:.5rem 0">by @${esc(ep.creator)}${creator.project_url ? ` · building <a href="${esc(creator.project_url)}" target="_blank" rel="noopener">${esc(creator.project_name || "their project")}</a>` : ""}</p>
      <p>${esc(ep.summary)}</p>
      <div class="proof-strip" style="margin:.875rem 0">${ep.proof?.verified ? `<span class="badge badge-success">Verified · ${ep.proof.hops} source hops</span>${ep.proof.quiz_correct ? `<span class="badge badge-info">Creator passed the quiz</span>` : ""}` : `<span class="badge badge-outline">No proof attached</span>`}<span class="badge ${ep.price_cents ? "badge-invert" : "badge-outline"}">${money(ep.price_cents)}</span></div>
      <div class="player">${ep.audio_path ? `<audio controls src="${esc(ep.audio_path)}"></audio>` : `<button id="narrateBtn" class="btn btn-primary"><svg><use href="#i-play"/></svg>Listen — browser narration</button><span class="text-xs muted">No uploaded audio. Narration is generated in your browser and labelled as such.</span>`}</div>
      ${ep.proof?.disclosure ? `<p class="text-xs muted" style="margin-top:.375rem">${esc(ep.proof.disclosure)}</p>` : ""}
      <div class="row wrap" style="margin-top:.875rem">
        ${ep.price_cents ? `<button id="buyBtn" class="btn btn-primary">Buy episode ${money(ep.price_cents)}</button>` : ""}
        <button id="tipBtn" class="btn btn-outline">Tip creator</button><button id="subBtn" class="btn btn-outline">Subscribe</button>
        <a class="btn btn-ghost" href="/rss/${esc(ep.creator)}.xml"><svg><use href="#i-rss"/></svg>RSS</a>
        <button id="shareBtn" class="btn btn-ghost">Copy share text</button>
      </div>
    </div></div>
    <div class="section-title"><h2>Verified code path</h2><span class="badge badge-outline">Check every line</span></div>
    <div class="frame"><div class="frame-panel"><ol class="timeline">${hops || "<li>No trace attached.</li>"}</ol></div></div>
    <div class="section-title"><h2>Transcript</h2></div>
    <div class="transcript-list">${turns}</div>
  </div>`;
  show("episode"); history.replaceState({}, "", "/e/" + id);
  $("tipBtn").onclick = () => checkout("tip", ep.creator);
  $("subBtn").onclick = () => checkout("sub", ep.creator);
  if ($("buyBtn")) $("buyBtn").onclick = () => checkout("episode", ep.creator, ep.id);
  $("shareBtn").onclick = () => navigator.clipboard.writeText(
    `I traced my own code out loud and published the proof: "${ep.title}" ${location.origin}/e/${ep.id} — every claim cites a real file:line. Built with Know Your Code.`);
  const narrate = $("narrateBtn");
  if (narrate) narrate.onclick = () => {
    if (!("speechSynthesis" in window)) { banner("Narration is not available in this browser."); return; }
    speechSynthesis.cancel();
    ep.transcript.forEach(t => { const u = new SpeechSynthesisUtterance((t.role === "user" ? "Creator: " : "Agent: ") + t.content.slice(0, 700)); speechSynthesis.speak(u); });
  };
}

// ---------- revenue ----------
async function loadRevenue() {
  const data = await api("/api/purchases");
  $("stripeState").innerHTML = data.stripe_configured
    ? `<div class="alert alert-success"><svg><use href="#i-shield"/></svg><span><strong>Stripe is live.</strong> Tips, subscriptions, and paid episodes run on hosted Checkout${$("stripeAccount").value.trim() ? " with payouts to your connected account (platform fee 10%)" : " — add your connected account below so payouts land with you"}.</span></div>`
    : `<div class="alert alert-warning"><svg><use href="#i-info"/></svg><span><strong>Stripe is not configured.</strong> No payment can be taken and nothing is faked. Restart with <span class="file-ref">STRIPE_SECRET_KEY=… python3 app/server.py</span>, then paste your Connect account id below.</span></div>`;
  const rows = data.purchases;
  const total = rows.reduce((sum, x) => sum + (x.amount_cents || 0), 0);
  $("revenueStats").innerHTML = [
    [dollars(total), "Confirmed revenue"], [rows.length, "Payments"],
    [rows.filter(x => x.kind === "sub").length, "Subscriptions"], [rows.filter(x => x.kind === "tip").length, "Tips"]
  ].map(([n, l]) => `<div class="frame"><div class="frame-panel stat"><div class="num">${n}</div><div class="lab">${l}</div></div></div>`).join("");
  $("salesOut").innerHTML = rows.length
    ? `<div class="table-wrap" style="border:0;border-radius:0"><table><thead><tr><th>When</th><th>Kind</th><th>Creator</th><th>Amount</th><th>Status</th></tr></thead><tbody>` +
      rows.map(x => `<tr><td>${esc(x.created_at)}</td><td><span class="badge">${esc(x.kind)}</span></td><td>@${esc(x.creator)}</td><td>${money(x.amount_cents)}</td><td><span class="badge badge-success">${esc(x.status)}</span></td></tr>`).join("") + "</tbody></table></div>"
    : `<div class="empty" style="border:0">No Stripe-confirmed sales yet. Publish an episode, share the link, and let the proof sell it.</div>`;
  const me = await api("/api/creators/" + handle()).catch(() => null);
  if (me?.creator) {
    $("cname").value = me.creator.name || ""; $("bio").value = me.creator.bio || "";
    $("projectName").value = me.creator.project_name || ""; $("projectUrl").value = me.creator.project_url || "";
    $("tipPrice").value = me.creator.tip_cents / 100; $("subPrice").value = me.creator.sub_cents / 100;
    $("stripeAccount").value = me.creator.stripe_account_id || "";
    $("whoName").textContent = me.creator.name || handle();
  }
}

// ---------- draft ----------
function saveDraft() {
  try { localStorage.setItem("kyc:draft", JSON.stringify({
    epTitle: $("epTitle").value, epSummary: $("epSummary").value, epPrice: $("epPrice").value,
    history: state.history.slice(-30), sessionId: state.sessionId, quizCorrect: state.quizCorrect,
    scanned: !!state.scanned, published: !!state.published })); } catch (e) { /* storage full/blocked: draft is best-effort */ }
}
function restoreDraft() {
  try {
    const d = JSON.parse(localStorage.getItem("kyc:draft") || "null"); if (!d) return false;
    $("epTitle").value = d.epTitle || ""; $("epSummary").value = d.epSummary || "";
    if (d.epPrice) $("epPrice").value = d.epPrice;
    state.sessionId = d.sessionId || null; state.quizCorrect = !!d.quizCorrect;
    state.scanned = !!d.scanned; state.published = !!d.published;
    (d.history || []).forEach(t => addTurn(t.role, t.content));
    return state.history.length > 0;
  } catch (e) { return false; }
}
["epTitle", "epSummary", "epPrice"].forEach(id => $(id).addEventListener("input", saveDraft));
window.addEventListener("popstate", () => {
  const ep = location.pathname.match(/^\/e\/(\d+)$/);
  if (ep) { openEpisode(+ep[1]); return; }
  const view = ["discover", "revenue"].includes(location.hash.slice(1)) ? location.hash.slice(1) : "studio";
  show(view);
});

// ---------- boot / routing ----------
(async function boot() {
  $("themeBtn").onclick = () => { const dark = document.documentElement.classList.toggle("dark"); localStorage.setItem("kyc:theme", dark ? "dark" : "light"); };
  $("topPublishBtn").onclick = () => { show("studio"); $("publishFrame").scrollIntoView({ behavior: "smooth", block: "center" }); $("epTitle").focus(); };
  $("sideStartBtn").onclick = () => { show("studio"); $("chatInput").focus(); sendChat("walkthrough", "What happens when I press Save? Follow it from the button to storage. Don't change any files."); };
  const health = await api("/api/health").catch(() => null);
  if (!health) { $("serverBadge").textContent = "server offline"; banner("Studio server unreachable. Start it with: python3 app/server.py"); return; }
  $("serverBadge").textContent = health.stripe_configured ? "Local · Stripe live" : "Local · Stripe off";
  await checkStripeReturn();
  const epMatch = location.pathname.match(/^\/e\/(\d+)$/);
  const crMatch = location.pathname.match(/^\/c\/([\w-]+)$/);
  if (epMatch) { await loadDiscover(); openEpisode(+epMatch[1]); }
  else if (crMatch) { show("discover"); await loadDiscover(); $("search").value = crMatch[1]; renderDiscover(crMatch[1]); }
  else if (["studio", "discover", "revenue"].includes(location.hash.slice(1))) show(location.hash.slice(1));
  else show("studio");
  const restored = restoreDraft(); if (typeof setSteps === "function") setSteps();
  if (!restored) addTurn("assistant", "Welcome to your Studio. I trace your real code — every claim cites a file and line, and I never change your files. Scan your project, then ask what happens when you press Save. When it clicks, hit Quiz me, record, and publish: the episode carries the proof.", "local");
  if (new URLSearchParams(location.search).has("autotrace")) sendChat("walkthrough", "What happens when I press Save? Follow it from the button to storage. Don't change any files.");
})();
