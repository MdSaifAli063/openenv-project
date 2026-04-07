"""Auxiliary server entrypoint required by OpenEnv local validation checks."""

from pathlib import Path
import sys

from flask import Flask, Response, jsonify, request

try:
    from .environment import EmailTriageEnv
except ImportError:
    SERVER_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = SERVER_DIR.parent
    for import_path in (str(SERVER_DIR), str(PROJECT_DIR)):
        if import_path not in sys.path:
            sys.path.insert(0, import_path)
    from environment import EmailTriageEnv

FRONTEND_HTML = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Inbox Helper Practice</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
        :root {
            --bg: #f3f7fb;
            --text: #16263d;
            --muted: #5e7087;
            --line: rgba(22, 38, 61, 0.12);
            --accent: #0f766e;
            --accent-strong: #115e59;
            --accent-soft: rgba(15, 118, 110, 0.12);
            --secondary: #24405d;
            --secondary-soft: rgba(36, 64, 93, 0.1);
            --ok-bg: #eaf8f4;
            --ok-text: #0e6a52;
            --err-bg: #fff1ee;
            --err-text: #b14628;
            --shadow: 0 24px 80px rgba(28, 53, 87, 0.12);
            --radius-xl: 28px;
            --radius-lg: 20px;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Manrope', sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(44, 181, 167, 0.18), transparent 28%),
                radial-gradient(circle at bottom right, rgba(35, 80, 147, 0.16), transparent 32%),
                linear-gradient(180deg, #f8fbfe 0%, var(--bg) 100%);
            min-height: 100vh;
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(255,255,255,0.24) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.24) 1px, transparent 1px);
            background-size: 32px 32px;
            mask-image: linear-gradient(180deg, rgba(0,0,0,0.4), transparent 90%);
        }
        .wrap {
            max-width: 1180px;
            margin: 0 auto;
            padding: 28px 18px 44px;
            animation: fade-up .55s ease-out;
        }
        @keyframes fade-up {
            from { opacity: 0; transform: translateY(14px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .hero {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: 1.3fr .9fr;
            gap: 20px;
            padding: 28px;
            margin-bottom: 18px;
            border: 1px solid rgba(255, 255, 255, 0.72);
            border-radius: var(--radius-xl);
            background: linear-gradient(140deg, rgba(12, 32, 53, 0.95), rgba(18, 83, 96, 0.9));
            color: #f4fbff;
            box-shadow: var(--shadow);
        }
        .hero::after {
            content: "";
            position: absolute;
            width: 300px;
            height: 300px;
            right: -80px;
            top: -110px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(115, 232, 214, 0.38), transparent 68%);
        }
        .eyebrow, .badge, .pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            font-size: .82rem;
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .eyebrow {
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.1);
        }
        .hero h1 {
            margin: 14px 0 10px;
            font-size: clamp(2rem, 4vw, 3.7rem);
            line-height: 1;
            letter-spacing: -.04em;
        }
        .subtitle {
            max-width: 640px;
            margin: 0;
            color: rgba(244, 251, 255, 0.8);
            line-height: 1.65;
        }
        .hero-side, .stack, .input-grid, .tips {
            display: grid;
            gap: 12px;
        }
        .badge {
            justify-self: start;
            padding: 9px 14px;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.14);
            color: #f8ffff;
            backdrop-filter: blur(10px);
        }
        .hero-note {
            padding: 16px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        .hero-note strong, .tip strong {
            display: block;
            margin-bottom: 6px;
            font-size: .95rem;
        }
        .hero-note p, .tip p, .section-copy {
            margin: 0;
            line-height: 1.55;
        }
        .dashboard {
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(320px, .9fr);
            gap: 18px;
            align-items: start;
        }
        .stack { gap: 18px; }
        .card {
            border: 1px solid var(--line);
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, 0.74);
            backdrop-filter: blur(20px);
            box-shadow: 0 18px 50px rgba(26, 46, 74, 0.08);
        }
        .card-body { padding: 20px; }
        .section-heading {
            margin: 0 0 6px;
            font-size: 1.08rem;
            font-weight: 800;
            letter-spacing: -.02em;
        }
        .section-copy {
            margin: 0 0 16px;
            color: var(--muted);
            font-size: .94rem;
        }
        .field label {
            display: block;
            margin-bottom: 8px;
            font-size: .82rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
            color: var(--muted);
        }
        select, input, textarea, button { font: inherit; }
        select, input, textarea {
            width: 100%;
            border: 1px solid rgba(23, 48, 76, 0.14);
            border-radius: 14px;
            padding: 13px 14px;
            background: rgba(255, 255, 255, 0.92);
            color: var(--text);
            outline: none;
            transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease;
        }
        select:focus, input:focus, textarea:focus {
            border-color: rgba(15, 118, 110, 0.55);
            box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.12);
            transform: translateY(-1px);
        }
        textarea {
            min-height: 130px;
            resize: vertical;
            line-height: 1.55;
        }
        .button-row, .mail-top {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            justify-content: space-between;
        }
        button {
            border: 0;
            border-radius: 14px;
            padding: 13px 16px;
            font-weight: 800;
            letter-spacing: -.01em;
            cursor: pointer;
            transition: transform .16s ease, box-shadow .16s ease, opacity .16s ease;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(16, 36, 58, 0.12);
        }
        button:active { transform: translateY(0); opacity: .92; }
        button.primary {
            background: linear-gradient(135deg, var(--accent), var(--accent-strong));
            color: #fff;
        }
        button.secondary {
            background: var(--secondary-soft);
            color: var(--secondary);
        }
        .status {
            display: flex;
            align-items: center;
            min-height: 52px;
            padding: 14px 16px;
            border-radius: 16px;
            background: var(--ok-bg);
            color: var(--ok-text);
            font-weight: 700;
            line-height: 1.45;
        }
        .status.error { background: var(--err-bg); color: var(--err-text); }
        .mail-shell {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,250,255,0.94));
        }
        .mail-top { padding: 18px 20px 0; }
        .pill {
            padding: 9px 12px;
            background: var(--accent-soft);
            color: var(--accent-strong);
        }
        .mail-card {
            margin: 14px 20px 20px;
            border: 1px solid rgba(23, 48, 76, 0.09);
            border-radius: 18px;
            background: #fff;
            overflow: hidden;
        }
        .mail-header {
            display: grid;
            gap: 14px;
            padding: 18px 18px 16px;
            border-bottom: 1px solid rgba(23, 48, 76, 0.08);
        }
        .mail-subject {
            margin: 0;
            font-size: 1.18rem;
            font-weight: 800;
            letter-spacing: -.02em;
        }
        .meta-line {
            display: grid;
            grid-template-columns: 74px 1fr;
            gap: 12px;
            align-items: start;
            font-size: .94rem;
        }
        .meta-label {
            color: var(--muted);
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
            font-size: .78rem;
        }
        .mail-body {
            padding: 18px;
            white-space: pre-wrap;
            line-height: 1.7;
            color: #243548;
        }
        .tip {
            padding: 14px;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(23, 48, 76, 0.08);
        }
        pre {
            margin: 0;
            padding: 18px;
            border-radius: 18px;
            background: #091420;
            color: #d9ebf7;
            border: 1px solid rgba(140, 184, 221, 0.14);
            max-height: 360px;
            overflow: auto;
            white-space: pre-wrap;
            font-family: 'JetBrains Mono', monospace;
            font-size: .84rem;
            line-height: 1.6;
        }
        @media (max-width: 980px) {
            .hero, .dashboard { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
            .wrap { padding: 16px 14px 26px; }
            .hero { padding: 20px; border-radius: 24px; }
            .meta-line { grid-template-columns: 1fr; gap: 4px; }
            .button-row button { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <section class="hero">
            <div>
                <span class="eyebrow">Email triage studio</span>
                <h1>Train faster with a calmer inbox workflow.</h1>
                <p class="subtitle">The backend logic stays exactly the same. This refreshed frontend gives you a cleaner way to review a message, choose the right owner, and submit a short decision with confidence.</p>
            </div>
            <div class="hero-side">
                <span class="badge" id="badge">connecting...</span>
                <div class="hero-note">
                    <strong>Simple flow</strong>
                    <p>Start a scenario, read the email, submit your decision, and use the advanced panel only when you need the raw response.</p>
                </div>
                <div class="hero-note">
                    <strong>What stays unchanged</strong>
                    <p>Routes, request payloads, environment behavior, and the project structure all remain untouched.</p>
                </div>
            </div>
        </section>
        <main class="dashboard">
            <div class="stack">
                <section class="card">
                    <div class="card-body">
                        <h2 class="section-heading">Start a scenario</h2>
                        <p class="section-copy">Pick a difficulty level and load a practice email.</p>
                        <div class="input-grid">
                            <div class="field">
                                <label for="taskId">Scenario</label>
                                <select id="taskId">
                                    <option value="task_easy">Easy: one clear email</option>
                                    <option value="task_medium">Medium: mixed inbox</option>
                                    <option value="task_hard">Hard: high-risk complaint</option>
                                </select>
                            </div>
                            <div class="button-row">
                                <button class="primary" id="btnReset">Start scenario</button>
                                <button class="secondary" id="btnState">Check progress</button>
                            </div>
                            <div class="status" id="status">Ready. Start a scenario.</div>
                        </div>
                    </div>
                </section>
                <section class="card mail-shell">
                    <div class="mail-top">
                        <div>
                            <h2 class="section-heading">Current email</h2>
                            <p class="section-copy">Read the message before you assign priority and routing.</p>
                        </div>
                        <span class="pill">Live scenario</span>
                    </div>
                    <div class="mail-card">
                        <div class="mail-header">
                            <h3 class="mail-subject" id="mailSubject">No email loaded yet.</h3>
                            <div class="meta-line">
                                <span class="meta-label">From</span>
                                <span id="mailSender">-</span>
                            </div>
                        </div>
                        <div class="mail-body" id="mailBody">Start a scenario to load an email.</div>
                    </div>
                </section>
                <section class="card">
                    <div class="card-body">
                        <h2 class="section-heading">Advanced details</h2>
                        <p class="section-copy">Raw response data is still available here for debugging and validation.</p>
                        <pre id="output">Waiting for your first action...</pre>
                    </div>
                </section>
            </div>
            <aside class="stack">
                <section class="card">
                    <div class="card-body">
                        <h2 class="section-heading">Your decision</h2>
                        <p class="section-copy">Choose the label, route it to the right team, and summarize the signal in one clear sentence.</p>
                        <div class="input-grid">
                            <div class="field">
                                <label for="label">Priority</label>
                                <select id="label">
                                    <option value="urgent">Urgent</option>
                                    <option value="normal" selected>Normal</option>
                                    <option value="spam">Spam</option>
                                    <option value="archive">Archive</option>
                                </select>
                            </div>
                            <div class="field">
                                <label for="routeTo">Route to</label>
                                <input id="routeTo" placeholder="billing, safety, engineering, support" value="general" />
                            </div>
                            <div class="field">
                                <label for="summary">Reason</label>
                                <textarea id="summary" placeholder="Write one clear sentence with key clues from the email.">Needs review.</textarea>
                            </div>
                            <div class="button-row">
                                <button class="primary" id="btnStep">Send decision</button>
                            </div>
                        </div>
                    </div>
                </section>
                <section class="card">
                    <div class="card-body">
                        <h2 class="section-heading">Quick reminders</h2>
                        <p class="section-copy">A lightweight checklist to keep the decision process consistent.</p>
                        <div class="tips">
                            <div class="tip">
                                <strong>Look for risk first</strong>
                                <p>Escalate safety, legal, billing, or urgent customer-impact issues before routine requests.</p>
                            </div>
                            <div class="tip">
                                <strong>Route with intent</strong>
                                <p>Pick the team that can actually resolve the issue instead of using a vague owner when the clues are clear.</p>
                            </div>
                            <div class="tip">
                                <strong>Keep summaries sharp</strong>
                                <p>One sentence is enough if it captures the sender, the issue, and the reason for the chosen label.</p>
                            </div>
                        </div>
                    </div>
                </section>
            </aside>
        </main>
    </div>
    <script>
        const statusEl = document.getElementById('status');
        const badgeEl = document.getElementById('badge');
        const outEl = document.getElementById('output');
        const mailSubjectEl = document.getElementById('mailSubject');
        const mailSenderEl = document.getElementById('mailSender');
        const mailBodyEl = document.getElementById('mailBody');
        function setStatus(msg, isError = false) {
            statusEl.textContent = msg;
            statusEl.classList.toggle('error', isError);
        }
        function writeOutput(value) {
            outEl.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
        }
        function updateEmailPanel(data) {
            if (!data || !data.observation) {
                return;
            }
            const obs = data.observation;
            mailSubjectEl.textContent = obs.subject || 'No subject';
            mailSenderEl.textContent = obs.sender || '-';
            mailBodyEl.textContent = obs.body || '';
        }
        async function postJson(path, payload) {
            const response = await fetch(path, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload || {}),
            });
            const text = await response.text();
            let data = text;
            try { data = JSON.parse(text); } catch (e) {}
            if (!response.ok) {
                throw new Error('HTTP ' + response.status + ' - ' + text);
            }
            return data;
        }
        async function warmup() {
            try {
                const res = await fetch('/meta');
                const data = await res.json();
                badgeEl.textContent = data.status === 'ok' ? 'ready' : 'check service';
            } catch (e) {
                badgeEl.textContent = 'offline';
            }
        }
        document.getElementById('btnReset').addEventListener('click', async () => {
            const taskId = document.getElementById('taskId').value;
            setStatus('Starting a new scenario...');
            try {
                const data = await postJson('/reset', { task_id: taskId });
                setStatus('Scenario started. Read the email below.');
                updateEmailPanel(data);
                writeOutput(data);
            } catch (e) {
                setStatus('Could not start scenario. See details below.', true);
                writeOutput(String(e));
            }
        });
        document.getElementById('btnState').addEventListener('click', async () => {
            setStatus('Checking progress...');
            try {
                const data = await postJson('/state', {});
                setStatus('Progress updated.');
                writeOutput(data);
            } catch (e) {
                setStatus('Could not fetch progress. See details below.', true);
                writeOutput(String(e));
            }
        });
        document.getElementById('btnStep').addEventListener('click', async () => {
            const payload = {
                label: document.getElementById('label').value,
                summary: document.getElementById('summary').value,
                route_to: document.getElementById('routeTo').value,
            };
            setStatus('Sending your decision...');
            try {
                const data = await postJson('/step', payload);
                setStatus('Decision saved.');
                updateEmailPanel(data);
                writeOutput(data);
            } catch (e) {
                setStatus('Could not submit decision. See details below.', true);
                writeOutput(String(e));
            }
        });
        warmup();
    </script>
</body>
</html>
"""

app = Flask(__name__)
current_env = EmailTriageEnv(task_id="task_easy")


@app.get("/")
@app.get("/web")
def root_page():
    """Render a lightweight frontend for interacting with the environment."""
    return Response(FRONTEND_HTML, mimetype="text/html")


@app.get("/meta")
def root_endpoint():
    """Return service metadata for health checks and machine clients."""
    return jsonify(
        {
            "name": "email-triage-env",
            "status": "ok",
            "endpoints": {
                "reset": {"method": "POST", "path": "/reset"},
                "step": {"method": "POST", "path": "/step"},
                "state": {"method": "POST", "path": "/state"},
            },
        }
    )


@app.get("/health")
def health_endpoint():
    """Return a simple health response for container checks."""
    return jsonify({"status": "ok"})


@app.post("/reset")
def reset_endpoint():
    """Reset the environment with a selected task and return ResetResult JSON."""
    global current_env

    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    elif not isinstance(payload, dict):
        return jsonify({"error": "Malformed JSON payload."}), 400

    task_id = payload.get("task_id", "task_easy")
    if not isinstance(task_id, str):
        return jsonify({"error": "Field 'task_id' must be a string."}), 400

    try:
        current_env = EmailTriageEnv(task_id=task_id)
        reset_result = current_env.reset()
    except KeyError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify(reset_result.model_dump())


@app.post("/step")
def step_endpoint():
    """Advance environment by one action and return StepResult JSON."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Malformed JSON payload."}), 400

    step_result = current_env.step(payload)
    return jsonify(step_result.model_dump())


@app.post("/state")
def state_endpoint():
    """Return read-only EnvironmentState JSON snapshot."""
    state_result = current_env.state()
    return jsonify(state_result.model_dump())


def main() -> None:
    """Run the Flask app for local and script-based launches."""
    app.run(host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
