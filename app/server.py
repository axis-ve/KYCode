"""KYCode Studio: local-first harness to talk with a codebase and publish proof episodes.

Run: python3 app/server.py  (http://127.0.0.1:8765)
Stdlib only. Read-only on target projects. BYOK keys are proxied per request, never stored.
"""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = Path(__file__).resolve().parent
STATIC = APP_DIR / "static"
MEDIA = APP_DIR / "media"
DB_PATH = Path(os.environ.get("KYC_DB", APP_DIR / "studio.db"))
SKILL_PATH = ROOT / "skills" / "know-your-code" / "SKILL.md"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".cursor", ".claude"}
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".rb", ".go", ".rs", ".java", ".php", ".html", ".md"}
MAX_FILE_BYTES = 400_000
PLATFORM_FEE_PERCENT = 10


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- database ----------
@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    MEDIA.mkdir(exist_ok=True)
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS creators(
          handle TEXT PRIMARY KEY, name TEXT, bio TEXT DEFAULT '', project_name TEXT DEFAULT '',
          project_url TEXT DEFAULT '', tip_cents INTEGER DEFAULT 500, sub_cents INTEGER DEFAULT 900,
          stripe_account_id TEXT DEFAULT '', created_at TEXT);
        CREATE TABLE IF NOT EXISTS episodes(
          id INTEGER PRIMARY KEY AUTOINCREMENT, creator TEXT, title TEXT, summary TEXT DEFAULT '',
          action TEXT DEFAULT '', transcript TEXT DEFAULT '[]', code_path TEXT DEFAULT '[]',
          checks TEXT DEFAULT '[]', quiz TEXT DEFAULT '{}', audio_path TEXT DEFAULT '',
          price_cents INTEGER DEFAULT 0, published INTEGER DEFAULT 0, demo INTEGER DEFAULT 0,
          created_at TEXT);
        CREATE TABLE IF NOT EXISTS trace_sessions(
          id TEXT PRIMARY KEY, project TEXT, repo_commit TEXT DEFAULT '', action TEXT DEFAULT '',
          hops TEXT DEFAULT '[]', checks TEXT DEFAULT '[]', quiz TEXT DEFAULT '{}',
          quiz_correct INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS purchases(
          id INTEGER PRIMARY KEY AUTOINCREMENT, episode_id INTEGER, creator TEXT, kind TEXT,
          amount_cents INTEGER, stripe_session_id TEXT UNIQUE, status TEXT, created_at TEXT);
        """)
        cols = [row["name"] for row in conn.execute("PRAGMA table_info(episodes)")]
        if "session_id" not in cols:
            conn.execute("ALTER TABLE episodes ADD COLUMN session_id TEXT DEFAULT ''")


# ---------- codebase engine (read-only) ----------
def resolve_project(raw):
    if not raw or not str(raw).strip():
        raise ValueError("Give a project folder path.")
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"Not a folder: {path.name}")
    allowed = (ROOT.resolve(), Path.home().resolve())
    if not any(path == base or path.is_relative_to(base) for base in allowed):
        raise ValueError("Project must be inside this repository or your home folder.")
    return path


def iter_source_files(project):
    for path in sorted(project.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in TEXT_EXT and path.stat().st_size <= MAX_FILE_BYTES:
            yield path


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


DEF_RE = re.compile(r"^\s*(?:def|function|func)\s+([A-Za-z_$][\w$]*)|^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")
CALL_RE = re.compile(r"(?:([A-Za-z_]\w*)\.)?([A-Za-z_]\w*)\s*\(")
LABEL_RE = re.compile(r"""["']([A-Za-z][A-Za-z ]{1,24})["']\s*[:=]\s*(?:[A-Za-z_]\w*\.)?([A-Za-z_]\w*)""")


def scan_project(project):
    files = list(iter_source_files(project))
    languages, functions, labels = {}, [], []
    for path in files:
        languages[path.suffix.lstrip(".") or "txt"] = languages.get(path.suffix.lstrip(".") or "txt", 0) + 1
        rel = path.relative_to(project).as_posix()
        for number, line in enumerate(read_lines(path), 1):
            match = DEF_RE.search(line)
            if match:
                functions.append({"name": match.group(1) or match.group(2), "file": rel, "line": number})
            label = LABEL_RE.search(line)
            if label and label.group(2).startswith(("on_", "handle", "press")):
                labels.append({"label": label.group(1), "handler": label.group(2), "file": rel, "line": number})
    count = len(files)
    size = "small" if count <= 50 else "medium" if count <= 400 else "large"
    return {"path": str(project), "file_count": count, "languages": languages,
            "functions": functions[:80], "entry_labels": labels[:20], "size_class": size,
            "files": [p.relative_to(project).as_posix() for p in files[:200]]}


def build_index(project):
    """Map function name -> definition, and collect every line for call search."""
    defs, corpus = {}, []
    for path in iter_source_files(project):
        rel = path.relative_to(project).as_posix()
        lines = read_lines(path)
        corpus.append((rel, lines))
        for number, line in enumerate(lines, 1):
            match = DEF_RE.search(line)
            if match:
                name = match.group(1) or match.group(2)
                start, end = number - 1, number
                while end < len(lines) and end < start + 25 and not re.match(r"(?:def|function|func)\s", lines[end]):
                    end += 1
                defs.setdefault(name, {"name": name, "file": rel, "line": number,
                                       "snippet": line.strip(), "body": lines[start:end]})
    return defs, corpus


def action_candidates(action):
    text = (action or "").strip()
    quoted = re.search(r"""["']([^"']{1,30})["']""", text)
    if quoted:
        return [quoted.group(1)]
    stop = {"What", "When", "Press", "Walk", "Tell", "Talk", "Explain", "Quiz", "Why", "How",
            "Give", "Show", "Follow", "Start", "Co-host", "Welcome", "Something", "Broken"}
    caps = [word for word in re.findall(r"\b[A-Z][a-z]{2,}\b", text) if word not in stop]
    if caps:
        return caps
    words = [w for w in re.findall(r"[A-Za-z]{3,}", text.lower())
             if w not in {"what", "happens", "when", "press", "the", "button", "walk", "through", "please", "quiz"}]
    return list(reversed(words)) or [text]



def trace_action(project, action):
    defs, corpus = build_index(project)
    candidates = action_candidates(action)
    keyword = candidates[0]
    hops, seen = [], set()
    entry_name = None
    # 1. visible label -> handler binding (skill rule: prefer the label the user sees).
    # Try each candidate word until one matches real code ("Quiz me on Save" -> Save).
    for candidate in candidates:
        for rel, lines in corpus:
            for number, line in enumerate(lines, 1):
                if candidate.lower() in line.lower():
                    match = LABEL_RE.search(line)
                    if match:
                        hops.append({"label": f'"{match.group(1)}" action', "file": rel, "line": number,
                                     "snippet": line.strip(), "kind": "entry", "verified": True})
                        entry_name, keyword = match.group(2), candidate
                        break
            if entry_name:
                break
        if entry_name:
            break
    # 2. fall back to a function whose name contains a candidate
    if not entry_name:
        for candidate in candidates:
            for name in defs:
                if candidate.lower() in name.lower():
                    entry_name, keyword = name, candidate
                    break
            if entry_name:
                break
    frontier = [entry_name] if entry_name else []
    depth = 0
    while frontier and depth < 3 and len(hops) < 14:
        next_frontier = []
        for name in frontier:
            if name in seen or name not in defs:
                continue
            seen.add(name)
            found = defs[name]
            hops.append({"label": f"{name}()", "file": found["file"], "line": found["line"],
                         "snippet": found["snippet"], "kind": "function", "verified": True})
            for body_line in found["body"]:
                for _mod, callee in CALL_RE.findall(body_line):
                    if callee in defs and callee not in seen and callee != name:
                        next_frontier.append(callee)
        frontier = next_frontier
        depth += 1
    # stored data: writes inside traced function bodies
    stored = []
    for name in seen:
        for body_line in defs[name]["body"]:
            if body_line.lstrip().startswith(("def ", "function ")):
                continue
            if re.search(r"(\[\w+\]\s*=|\.append\(|\.write\(|INSERT|localStorage|put\(|save\()", body_line):
                stored.append({"file": defs[name]["file"], "detail": body_line.strip()})
    # reach: other call sites of traced functions
    reach = []
    for name in sorted(seen):
        callers = []
        for rel, lines in corpus:
            for number, line in enumerate(lines, 1):
                if re.search(rf"\b{re.escape(name)}\s*\(", line) and not DEF_RE.search(line):
                    callers.append(f"{rel}:{number}")
        reach.append({"function": name, "call_sites": callers[:8], "count": len(callers)})
    checks = suggest_checks(project, keyword, corpus)
    return {"action": action, "keyword": keyword, "hops": hops, "stored_data": stored[:6],
            "also_reached_by": reach, "checks": checks,
            "note": "Every hop read from source above. Checks are suggested, not run, unless you run them."}


def suggest_checks(project, keyword, corpus):
    checks = []
    rel_names = [rel for rel, _ in corpus]
    if any(name.startswith("test") or "/test" in name for name in rel_names):
        checks.append({"label": "Run the project tests", "command": "python3 -m unittest discover -v", "ran": False})
    for rel, lines in corpus:
        for line in lines:
            if "def press(" in line:
                checks.append({"label": f"Press {keyword} in the fixture entry point",
                               "command": f'python3 -B -c "import app; print(app.press(\'{keyword}\'))"',
                               "ran": False})
                return checks
    if not checks:
        checks.append({"label": "Search callers of the first traced function",
                       "command": f'grep -rn "{keyword.lower()}" .', "ran": False})
    return checks


# ---------- agent ----------
def skill_prompt():
    try:
        return SKILL_PATH.read_text(encoding="utf-8")[:6000]
    except OSError:
        return "Ground every claim in the supplied source. Separate read, ran, and inferred."


def local_walkthrough(trace):
    hops = trace["hops"]
    if not hops:
        return (f"I searched this project for \"{trace['keyword']}\" and could not find a label or "
                "function to start from. Try naming the exact button or action you see in the app. "
                "Nothing was changed; this is read-only.")
    parts = [f"This path has {len(hops)} step{'s' if len(hops) != 1 else ''}, starting at {hops[0]['label']}."]
    for index, hop in enumerate(hops, 1):
        parts.append(f"Step {index}: {hop['label']} — in {hop['file']} at line {hop['line']}: {hop['snippet']}")
    if trace["stored_data"]:
        parts.append("Where it lands: " + "; ".join(item["detail"] for item in trace["stored_data"][:3]) + ".")
    shared = [r for r in trace["also_reached_by"] if r["count"] > 1]
    if shared:
        parts.append("Worth knowing: " + ", ".join(f"{r['function']} is called from {r['count']} places" for r in shared[:3])
                     + ", so a change there reaches further than this one action.")
    parts.append("That is the whole path as read from source. Say 'less jargon', 'go deeper', or 'quiz me' any time.")
    return " ".join(parts)


def make_quiz(trace):
    funcs = [h for h in trace["hops"] if h["kind"] == "function"]
    if not funcs:
        return None
    target = funcs[-1]
    name = target["label"].rstrip("()")
    return {"question": (f"One question to prove it stuck: when this action runs, which function is the "
                         f"last one on the path we traced, and which file is it in? Answer in your own words."),
            "expected": name, "expected_file": target["file"],
            "explain": f"The last traced function is {name}() in {target['file']}:{target['line']}."}


def grade_quiz(quiz, answer):
    text = (answer or "").lower()
    correct = quiz.get("expected", "").lower() in text
    if correct:
        return {"correct": True, "reply": f"Correct. {quiz.get('explain', '')} That answer is now your proof on the episode."}
    return {"correct": False, "reply": f"Not quite. {quiz.get('explain', '')} Want me to walk that last step again, slower?"}


def call_provider(provider, api_key, model, system, messages):
    if provider == "anthropic":
        payload = {"model": model or "claude-sonnet-4-5", "max_tokens": 1200, "system": system,
                   "messages": [{"role": m["role"], "content": m["content"]} for m in messages]}
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
        return "".join(block.get("text", "") for block in data.get("content", []))
    payload = {"model": model or "gpt-4o-mini", "max_tokens": 1200,
               "messages": [{"role": "system", "content": system}] + messages}
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    return data["choices"][0]["message"]["content"]


def chat_turn(project, message, history, mode, provider, api_key, model, quiz=None, session_id=None):
    if mode == "quiz-answer":
        session = get_trace_session(session_id) if session_id else None
        stored = (session or {}).get("quiz") or quiz
        if not stored:
            trace = trace_action(project, message)
            return {"reply": "That quiz session is gone, so I cannot grade it honestly. Ask for a new quiz.",
                    "trace": trace, "source": "local", "session_id": create_trace_session(project, trace),
                    "resume_point": "quiz session expired"}
        graded = grade_quiz(stored, message)
        if session:
            with db() as conn:
                conn.execute("UPDATE trace_sessions SET quiz_correct=? WHERE id=?",
                             (1 if graded["correct"] else 0, session_id))
        trace = trace_action(project, stored.get("expected_file", message))
        return {"reply": graded["reply"], "trace": trace, "quiz_result": graded, "source": "local",
                "session_id": session_id, "resume_point": "quiz answered"}
    trace = trace_action(project, message)
    if mode == "quiz":
        made = make_quiz(trace)
        if made:
            new_session = create_trace_session(project, trace, quiz=made)
            return {"reply": made["question"], "trace": trace,
                    "quiz": {"question": made["question"]}, "source": "local",
                    "session_id": new_session, "resume_point": "waiting for your quiz answer"}
        mode = "walkthrough"
    context = json.dumps({"hops": trace["hops"], "stored_data": trace["stored_data"],
                          "also_reached_by": trace["also_reached_by"]}, indent=1)
    framing = {"walkthrough": "Lead a voice walkthrough of this action.",
               "diagnose": "Investigate this symptom. Reproduce before naming a cause; label hypotheses.",
               "cohost": "You are co-hosting a short podcast episode about this code. Be conversational, "
                         "ask the creator one sharp question at the end, stay grounded in the evidence."}.get(mode, "")
    if api_key:
        system = (skill_prompt() + f"\n\nMODE: {framing}\nVERIFIED TRACE (cite file:line from this only):\n{context}\n"
                  "Speak in connected conversational sections. Do not invent files or runs. "
                  "Label anything not in the trace as inference.")
        messages = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in (history or [])][-8:]
        messages.append({"role": "user", "content": message})
        try:
            reply = call_provider(provider or "openai", api_key, model, system, messages)
            return {"reply": reply, "trace": trace, "source": provider or "openai",
                    "session_id": create_trace_session(project, trace),
                    "resume_point": f"{len(trace['hops'])}-step path traced"}
        except Exception as error:  # honest fallback, never a fake model answer
            return {"reply": local_walkthrough(trace), "trace": trace, "source": "local-fallback",
                    "session_id": create_trace_session(project, trace),
                    "provider_error": str(error)[:300], "resume_point": f"{len(trace['hops'])}-step path traced"}
    reply = local_walkthrough(trace)
    if mode == "diagnose":
        reply = ("Before naming a cause, here is the path your symptom must travel — reproduce it along this "
                 "path first, then we bisect it. " + reply)
    if mode == "cohost":
        reply = ("Welcome back to the show. Today we open the hood on your own code. " + reply +
                 " So, creator to creator: which of these steps surprised you most?")
    return {"reply": reply, "trace": trace, "source": "local",
            "session_id": create_trace_session(project, trace),
            "resume_point": f"{len(trace['hops'])}-step path traced"}


PROOF_DISCLOSURE = ("Verified means the server traced these exact file:line hops and hashed the snippets "
                    "at the recorded commit. It does not prove the creator wrote the code, that unquizzed "
                    "parts are understood, or that the code still matches today.")


def repo_commit(project):
    try:
        out = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def attest_hops(hops):
    return [{**hop, "sha256": hashlib.sha256(
        f"{hop['file']}:{hop['line']}:{hop['snippet']}".encode()).hexdigest()} for hop in hops]


def create_trace_session(project, trace, quiz=None):
    session_id = secrets.token_urlsafe(18)
    with db() as conn:
        conn.execute("INSERT INTO trace_sessions(id,project,repo_commit,action,hops,checks,quiz,created_at)"
                     " VALUES(?,?,?,?,?,?,?,?)",
                     (session_id, project.name, repo_commit(project), trace.get("action", ""),
                      json.dumps(attest_hops(trace["hops"])), json.dumps(trace["checks"]),
                      json.dumps(quiz or {}), now()))
    return session_id


def get_trace_session(session_id):
    with db() as conn:
        row = conn.execute("SELECT * FROM trace_sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        return None
    session = dict(row)
    for key, fallback in (("hops", []), ("checks", []), ("quiz", {})):
        try:
            session[key] = json.loads(session.get(key) or json.dumps(fallback))
        except (TypeError, json.JSONDecodeError):
            session[key] = fallback
    return session


def parse_range(header, size):
    if not header or size <= 0:
        return None
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
    if not match or (not match.group(1) and not match.group(2)):
        return None
    if match.group(1) == "":
        count = int(match.group(2))
        return (max(size - count, 0), size - 1) if count > 0 else None
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else size - 1
    if start > end or start >= size:
        return None
    return (start, min(end, size - 1))


def create_episode(body):
    """Proof fields come only from a server trace session; client hops never verify."""
    session_id = body.get("session_id") or ""
    code_path, checks, quiz = [], [], {}
    if session_id:
        session = get_trace_session(session_id)
        if not session:
            raise ValueError("Unknown trace session. Talk with your codebase first, then publish.")
        code_path, checks = session["hops"], session["checks"]
        stored_quiz = session.get("quiz") or {}
        quiz = {"question": stored_quiz.get("question", ""),
                "correct": bool(session.get("quiz_correct"))}
    elif body.get("code_path"):
        code_path = body.get("code_path")  # kept as an unverified path, labelled as such
    with db() as conn:
        cursor = conn.execute(
            "INSERT INTO episodes(creator,title,summary,action,transcript,code_path,checks,quiz,"
            "price_cents,published,session_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (body.get("creator", "demo"), body.get("title", "Untitled episode"),
             body.get("summary", ""), body.get("action", ""), json.dumps(body.get("transcript", [])),
             json.dumps(code_path), json.dumps(checks), json.dumps(quiz),
             int(body.get("price_cents", 0)), 1 if body.get("published") else 0, session_id, now()))
        return cursor.lastrowid


# ---------- store ----------
def row_to_episode(row):
    episode = dict(row)
    for key, fallback in (("transcript", []), ("code_path", []), ("checks", []), ("quiz", {})):
        try:
            episode[key] = json.loads(episode.get(key) or json.dumps(fallback))
        except (TypeError, json.JSONDecodeError):
            episode[key] = fallback
    episode["published"] = bool(episode["published"])
    episode["demo"] = bool(episode.get("demo"))
    quiz = episode["quiz"] if isinstance(episode["quiz"], dict) else {}
    session_id = episode.get("session_id") or ""
    verified = bool(session_id and episode["code_path"])
    episode["proof"] = {"verified": verified, "hops": len(episode["code_path"]) if verified else 0,
                        "quiz_correct": bool(quiz.get("correct")) if verified else False,
                        "session_id": session_id, "disclosure": PROOF_DISCLOSURE}
    return episode


def get_creator(handle):
    with db() as conn:
        row = conn.execute("SELECT * FROM creators WHERE handle=?", (handle,)).fetchone()
    return dict(row) if row else None


def list_episodes(published_only=True, creator=None):
    query, args = "SELECT * FROM episodes", []
    clauses = []
    if published_only:
        clauses.append("published=1")
    if creator:
        clauses.append("creator=?")
        args.append(creator)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC"
    with db() as conn:
        rows = conn.execute(query, args).fetchall()
    return [row_to_episode(row) for row in rows]


def get_episode(episode_id):
    with db() as conn:
        row = conn.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
    return row_to_episode(row) if row else None


def seed_demo():
    with db() as conn:
        if conn.execute("SELECT COUNT(*) AS n FROM episodes").fetchone()["n"]:
            return
    fixture = ROOT / "evals" / "fixtures" / "notes-app"
    if not fixture.is_dir():
        return
    trace = trace_action(fixture, "What happens when I press Save?")
    walk = local_walkthrough(trace)
    session_id = create_trace_session(fixture, trace, quiz=make_quiz(trace))
    quiz = {"question": (make_quiz(trace) or {}).get("question", ""), "correct": False}
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO creators(handle,name,bio,project_name,created_at) VALUES(?,?,?,?,?)",
                     ("demo", "Demo Creator", "Seeded from a real trace of the notes-app eval fixture.",
                      "Notes App (eval fixture)", now()))
        conn.execute(
            "INSERT INTO episodes(creator,title,summary,action,transcript,code_path,checks,quiz,price_cents,"
            "published,demo,session_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,1,1,?,?)",
            ("demo", "What really happens when you press Save",
             "Demo episode: a real, source-traced walkthrough of the notes-app fixture in this repo. "
             "Record your own in the Studio.", "Press Save",
             json.dumps([{"role": "user", "content": "What happens when I press Save?"},
                         {"role": "assistant", "content": walk}]),
             json.dumps(attest_hops(trace["hops"])), json.dumps(trace["checks"]), json.dumps(quiz), 0, session_id, now()))


# ---------- stripe (hosted Checkout + Connect; honest when unconfigured) ----------
def stripe_configured():
    return bool(os.environ.get("STRIPE_SECRET_KEY"))


def stripe_request(method, path, form=None):
    data = urllib.parse.urlencode(form or {}, doseq=True).encode() if form else None
    request = urllib.request.Request(f"https://api.stripe.com/v1{path}", data=data, method=method,
                                     headers={"Authorization": f"Bearer {os.environ['STRIPE_SECRET_KEY']}",
                                              "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def create_checkout(kind, creator, episode, base_url):
    if not stripe_configured():
        return {"configured": False,
                "message": "Set STRIPE_SECRET_KEY to enable real payments. Nothing was charged."}
    amounts = {"tip": creator["tip_cents"], "sub": creator["sub_cents"],
               "episode": (episode or {}).get("price_cents", 0)}
    amount = int(amounts.get(kind, 0))
    if amount <= 0:
        return {"configured": True, "error": "This item is free or has no price set."}
    names = {"tip": f"Tip for @{creator['handle']}", "sub": f"Subscribe to @{creator['handle']}",
             "episode": (episode or {}).get("title", "Episode")}
    form = {"mode": "subscription" if kind == "sub" else "payment",
            "success_url": f"{base_url}/?paid=1&session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{base_url}/?paid=0",
            "line_items[0][quantity]": 1,
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": amount,
            "line_items[0][price_data][product_data][name]": names[kind],
            "metadata[kind]": kind, "metadata[creator]": creator["handle"],
            "metadata[episode_id]": str((episode or {}).get("id") or "")}
    if kind == "sub":
        form["line_items[0][price_data][recurring][interval]"] = "month"
    account = creator.get("stripe_account_id")
    if account and kind != "sub":
        form["payment_intent_data[transfer_data][destination]"] = account
        form["payment_intent_data[application_fee_amount]"] = amount * PLATFORM_FEE_PERCENT // 100
    if account and kind == "sub":
        form["subscription_data[transfer_data][destination]"] = account
        form["subscription_data[application_fee_percent]"] = PLATFORM_FEE_PERCENT
    session = stripe_request("POST", "/checkout/sessions", form)
    return {"configured": True, "url": session["url"], "session_id": session["id"]}


def verify_checkout(session_id):
    if not stripe_configured() or not session_id:
        return {"verified": False}
    session = stripe_request("GET", f"/checkout/sessions/{urllib.parse.quote(session_id)}")
    if session.get("payment_status") != "paid":
        return {"verified": False, "status": session.get("payment_status")}
    meta = session.get("metadata") or {}
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO purchases(episode_id,creator,kind,amount_cents,stripe_session_id,"
                     "status,created_at) VALUES(?,?,?,?,?,?,?)",
                     (int(meta["episode_id"]) if meta.get("episode_id") else None, meta.get("creator"),
                      meta.get("kind"), session.get("amount_total"), session_id, "paid", now()))
    return {"verified": True, "kind": meta.get("kind"), "creator": meta.get("creator"),
            "amount_cents": session.get("amount_total")}


# ---------- http ----------
class Handler(BaseHTTPRequestHandler):
    server_version = "KYCStudio/1.0"

    def log_message(self, *_args):
        pass

    def security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.security_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_bytes(self, body, content_type, status=200, cache="no-cache", etag=""):
        if etag and self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.end_headers()
            return
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        if etag:
            self.send_header("ETag", etag)
        if "text/html" in content_type:
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; img-src 'self' data:; media-src 'self' blob:; "
                             "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
        self.security_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_media(self, media):
        types = {".webm": "audio/webm", ".mp4": "audio/mp4", ".m4a": "audio/mp4", ".ogg": "audio/ogg"}
        data = media.read_bytes()
        content_type = types.get(media.suffix, "application/octet-stream")
        span = parse_range(self.headers.get("Range"), len(data))
        self.send_response(206 if span else 200)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "private, max-age=3600")
        self.security_headers()
        if span:
            start, end = span
            chunk = data[start:end + 1]
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(data)}")
            self.send_header("Content-Length", str(len(chunk)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(chunk)
        else:
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def base_url(self):
        return f"http://{self.headers.get('Host', '127.0.0.1:8765')}"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path, query = parsed.path, urllib.parse.parse_qs(parsed.query)
        try:
            if path == "/api/health":
                return self.send_json({"ok": True, "stripe_configured": stripe_configured(),
                                       "demo_project": "evals/fixtures/notes-app"})
            if path == "/api/episodes":
                return self.send_json({"episodes": list_episodes(
                    published_only=query.get("all", ["0"])[0] != "1", creator=query.get("creator", [None])[0])})
            match = re.fullmatch(r"/api/episodes/(\d+)", path)
            if match:
                episode = get_episode(int(match.group(1)))
                return self.send_json({"episode": episode} if episode else {"error": "not found"},
                                      200 if episode else 404)
            if path == "/api/creators":
                with db() as conn:
                    rows = conn.execute("SELECT * FROM creators ORDER BY handle").fetchall()
                return self.send_json({"creators": [dict(row) for row in rows]})
            match = re.fullmatch(r"/api/creators/([\w-]+)", path)
            if match:
                creator = get_creator(match.group(1))
                return self.send_json({"creator": creator} if creator else {"error": "not found"},
                                      200 if creator else 404)
            if path == "/api/purchases":
                with db() as conn:
                    rows = conn.execute("SELECT * FROM purchases ORDER BY id DESC").fetchall()
                return self.send_json({"purchases": [dict(row) for row in rows],
                                       "stripe_configured": stripe_configured()})
            if path == "/api/stripe/verify":
                return self.send_json(verify_checkout(query.get("session_id", [""])[0]))
            match = re.fullmatch(r"/rss/([\w-]+)\.xml", path)
            if match:
                return self.send_rss(match.group(1))
            match = re.fullmatch(r"/media/([\w.-]+)", path)
            if match:
                media = (MEDIA / match.group(1)).resolve()
                if media.is_relative_to(MEDIA.resolve()) and media.is_file():
                    return self.send_media(media)
                return self.send_json({"error": "not found"}, 404)
            match = re.fullmatch(r"/embed/(\d+)", path)
            if match:
                return self.send_embed(int(match.group(1)))
            if path in ("/", "/index.html") or re.fullmatch(r"/e/\d+", path) or re.fullmatch(r"/c/[\w-]+", path):
                return self.send_bytes((STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            static = (STATIC / path.lstrip("/")).resolve()
            if static.is_relative_to(STATIC.resolve()) and static.is_file():
                types = {".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml"}
                etag = '"' + hashlib.sha256(static.read_bytes()).hexdigest()[:16] + '"'
                return self.send_bytes(static.read_bytes(), types.get(static.suffix, "application/octet-stream"),
                                       etag=etag)
            return self.send_json({"error": "not found"}, 404)
        except (ValueError, KeyError, OSError) as error:
            return self.send_json({"error": str(error)}, 400)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            match = re.fullmatch(r"/api/episodes/(\d+)/audio", path)
            if match:
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0 or length > 80_000_000:
                    return self.send_json({"error": "empty or oversized audio"}, 400)
                ctype = (self.headers.get("Content-Type") or "").lower()
                ext = ".mp4" if "mp4" in ctype else ".ogg" if "ogg" in ctype else ".webm"
                name = f"ep{match.group(1)}{ext}"
                (MEDIA / name).write_bytes(self.rfile.read(length))
                with db() as conn:
                    conn.execute("UPDATE episodes SET audio_path=? WHERE id=?", (f"/media/{name}", int(match.group(1))))
                return self.send_json({"audio_path": f"/media/{name}"})
            body = self.read_json()
            if path == "/api/project/scan":
                return self.send_json(scan_project(resolve_project(body.get("path"))))
            if path == "/api/trace":
                return self.send_json(trace_action(resolve_project(body.get("path")), body.get("action", "")))
            if path == "/api/chat":
                return self.send_json(chat_turn(
                    resolve_project(body.get("path")), body.get("message", ""), body.get("history", []),
                    body.get("mode", "walkthrough"), self.headers.get("X-Provider"),
                    self.headers.get("X-Api-Key"), self.headers.get("X-Model"), quiz=body.get("quiz"), session_id=body.get("session_id")))
            if path == "/api/creators":
                handle = re.sub(r"[^\w-]", "", (body.get("handle") or "").lower())
                if not handle:
                    return self.send_json({"error": "handle required"}, 400)
                with db() as conn:
                    conn.execute(
                        "INSERT INTO creators(handle,name,bio,project_name,project_url,tip_cents,sub_cents,"
                        "stripe_account_id,created_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(handle) DO UPDATE SET "
                        "name=excluded.name,bio=excluded.bio,project_name=excluded.project_name,"
                        "project_url=excluded.project_url,tip_cents=excluded.tip_cents,sub_cents=excluded.sub_cents,"
                        "stripe_account_id=excluded.stripe_account_id",
                        (handle, body.get("name", handle), body.get("bio", ""), body.get("project_name", ""),
                         body.get("project_url", ""), int(body.get("tip_cents", 500)),
                         int(body.get("sub_cents", 900)), body.get("stripe_account_id", ""), now()))
                return self.send_json({"creator": get_creator(handle)})
            if path == "/api/episodes":
                return self.send_json({"episode": get_episode(create_episode(body))}, 201)
            match = re.fullmatch(r"/api/episodes/(\d+)/publish", path)
            if match:
                with db() as conn:
                    conn.execute("UPDATE episodes SET published=1 WHERE id=?", (int(match.group(1)),))
                return self.send_json({"episode": get_episode(int(match.group(1)))})
            if path == "/api/stripe/checkout":
                creator = get_creator(body.get("creator", ""))
                if not creator:
                    return self.send_json({"error": "creator not found"}, 404)
                episode = get_episode(int(body["episode_id"])) if body.get("episode_id") else None
                return self.send_json(create_checkout(body.get("kind", "tip"), creator, episode, self.base_url()))
            return self.send_json({"error": "not found"}, 404)
        except (ValueError, KeyError, TypeError, OSError) as error:
            return self.send_json({"error": str(error)}, 400)

    def send_rss(self, handle):
        creator = get_creator(handle)
        if not creator:
            return self.send_json({"error": "not found"}, 404)
        items = []
        for episode in list_episodes(creator=handle):
            audio = (f'<enclosure url="{self.base_url()}{episode["audio_path"]}" type="audio/webm"/>'
                     if episode.get("audio_path") else "")
            items.append(f"<item><title>{xml_escape(episode['title'])}</title>"
                         f"<link>{self.base_url()}/e/{episode['id']}</link>"
                         f"<guid>{self.base_url()}/e/{episode['id']}</guid>"
                         f"<description>{xml_escape(episode['summary'])}</description>"
                         f"<pubDate>{xml_escape(episode['created_at'])}</pubDate>{audio}</item>")
        rss = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
               f"<title>{xml_escape(creator['name'])} — Know Your Code</title>"
               f"<link>{self.base_url()}/c/{handle}</link>"
               f"<description>{xml_escape(creator['bio'] or 'Talking with my codebase, with proof.')}</description>"
               + "".join(items) + "</channel></rss>")
        return self.send_bytes(rss.encode(), "application/rss+xml; charset=utf-8")

    def send_embed(self, episode_id):
        episode = get_episode(episode_id)
        if not episode:
            return self.send_json({"error": "not found"}, 404)
        audio = (f'<audio controls src="{episode["audio_path"]}" style="width:100%"></audio>'
                 if episode.get("audio_path") else "<p>Listen with narration on the episode page.</p>")
        hops = " → ".join(hop["label"] for hop in episode["code_path"][:6])
        html = (f"<!doctype html><meta charset=utf-8><title>{xml_escape(episode['title'])}</title>"
                "<body style='font-family:system-ui;background:#fff;color:#171717;padding:16px'>"
                f"<strong>{xml_escape(episode['title'])}</strong><p>{xml_escape(episode['summary'])}</p>{audio}"
                f"<p style='opacity:.75;font-size:13px'>Verified code path: {xml_escape(hops)}</p>"
                f"<a style='color:#171717;font-weight:600' href='{self.base_url()}/e/{episode_id}' target='_blank'>Open episode with proof</a>")
        return self.send_bytes(html.encode(), "text/html; charset=utf-8")


def main():
    init_db()
    seed_demo()
    port = int(os.environ.get("KYC_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"KYCode Studio: http://127.0.0.1:{port}/  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
