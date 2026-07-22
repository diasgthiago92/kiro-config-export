#!/usr/bin/env python3
"""
sprint_confluence_watcher.py
Detecta sprint finalizada no Jira e publica/atualiza documentação no Confluence.
Roda 2x/dia via cron (9h e 17h). Usa state file para evitar duplicatas.
"""
import json, os, subprocess, sys
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
BOARD_ID       = 1358
PARENT_PAGE_ID = "7214432314"
CONFLUENCE_SPACE = "APS1"
SLACK_CHANNEL  = "C0B2X8FQ81M"
STATE_FILE     = os.path.expanduser("~/sprint_confluence_watcher.state")
LOG_FILE       = os.path.expanduser("~/sprint_confluence_watcher.log")
ENV_FILE       = os.path.expanduser("~/Documents/Brain/.env")

ATLASSIAN_BRIDGE = os.path.expanduser("~/Documents/Main/Brain/Bridges/atlassian_bridge.py")
SLACK_BRIDGE     = os.path.expanduser("~/Documents/Main/Brain/Bridges/slack_bridge.py")

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_env():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

def atlassian_call(tool, **args):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    })
    r = subprocess.run(
        ["python3", ATLASSIAN_BRIDGE],
        input=payload, capture_output=True, text=True
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"Bridge error: {r.stderr}")
    return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])

def slack_notify(text):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "send_message", "arguments": {"channel": SLACK_CHANNEL, "text": text}}
    })
    subprocess.run(
        ["python3", SLACK_BRIDGE],
        input=payload, capture_output=True, text=True
    )

# ── State ─────────────────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"published_sprints": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ── Sprint detection ──────────────────────────────────────────────────────────
def get_closed_sprints():
    """Retorna sprints com state=closed do board."""
    import requests, base64
    url = os.environ.get("ATLASSIAN_URL", "").rstrip("/")
    email = os.environ.get("ATLASSIAN_EMAIL", "")
    token = os.environ.get("ATLASSIAN_TOKEN", "")
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

    resp = requests.get(
        f"{url}/rest/agile/1.0/board/{BOARD_ID}/sprint",
        params={"state": "closed"},
        headers=headers
    )
    resp.raise_for_status()
    return resp.json().get("values", [])

def get_sprint_issues(sprint_id):
    return atlassian_call("jira_get_sprint_issues", sprint_id=sprint_id, board_id=BOARD_ID)

# ── Confluence page builder ───────────────────────────────────────────────────
def build_page_html(sprint, issues):
    name = sprint.get("name", "Sprint")
    start = sprint.get("startDate", "")[:10]
    end   = sprint.get("endDate", "")[:10]

    done, not_done = [], []
    for i in (issues if isinstance(issues, list) else issues.get("issues", [])):
        status = (i.get("status") or i.get("fields", {}).get("status", {}).get("name", "")).lower()
        if "done" in status or "conclu" in status:
            done.append(i)
        else:
            not_done.append(i)

    def issue_rows(lst):
        rows = ""
        for i in lst:
            key     = i.get("key", "")
            summary = i.get("summary") or i.get("fields", {}).get("summary", "")
            assignee = i.get("assignee") or i.get("fields", {}).get("assignee") or {}
            if isinstance(assignee, dict):
                assignee = assignee.get("displayName", "—")
            status  = i.get("status") or i.get("fields", {}).get("status", {}).get("name", "")
            rows += f"<tr><td><a href='https://olxbr.atlassian.net/browse/{key}'>{key}</a></td><td>{summary}</td><td>{assignee}</td><td>{status}</td></tr>"
        return rows

    total = len(done) + len(not_done)
    pct   = round(len(done) / total * 100) if total else 0

    html = f"""
<h1>{name}</h1>
<p><strong>Período:</strong> {start} → {end}</p>
<p><strong>Conclusão:</strong> {len(done)}/{total} issues ({pct}%)</p>

<h2>✅ Concluídas ({len(done)})</h2>
<table><tbody>
<tr><th>Issue</th><th>Resumo</th><th>Responsável</th><th>Status</th></tr>
{issue_rows(done)}
</tbody></table>

<h2>🔄 Não concluídas ({len(not_done)})</h2>
<table><tbody>
<tr><th>Issue</th><th>Resumo</th><th>Responsável</th><th>Status</th></tr>
{issue_rows(not_done)}
</tbody></table>

<p><em>Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}</em></p>
"""
    return html

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    load_env()
    state = load_state()
    published = set(state["published_sprints"])

    log("Verificando sprints finalizadas...")

    try:
        closed = get_closed_sprints()
    except Exception as e:
        log(f"ERRO ao buscar sprints: {e}")
        slack_notify(f"⚠️ sprint_confluence_watcher: erro ao buscar sprints — {e}")
        sys.exit(1)

    new_count = 0
    for sprint in closed:
        sid  = str(sprint["id"])
        name = sprint.get("name", sid)

        if sid in published:
            log(f"Sprint {name} já publicada, pulando.")
            continue

        log(f"Sprint finalizada detectada: {name} (id={sid})")

        try:
            issues = get_sprint_issues(int(sid))
            html   = build_page_html(sprint, issues)

            # Verifica se já existe página com esse título
            search = atlassian_call("confluence_search", query=f'title="{name}" AND space="{CONFLUENCE_SPACE}"', limit=1)
            existing = search.get("results", []) if isinstance(search, dict) else []

            if existing:
                page_id = existing[0]["id"]
                atlassian_call("confluence_update_page", page_id=page_id, title=name, content_html=html)
                action = "atualizada"
                page_url = f"https://olxbr.atlassian.net/wiki/spaces/{CONFLUENCE_SPACE}/pages/{page_id}"
            else:
                result = atlassian_call("confluence_create_page", title=name, content_html=html, parent_id=PARENT_PAGE_ID)
                page_id = result.get("id", "")
                action = "criada"
                page_url = f"https://olxbr.atlassian.net/wiki/spaces/{CONFLUENCE_SPACE}/pages/{page_id}"

            log(f"Página {action}: {page_url}")
            slack_notify(f"📋 Documentação da *{name}* {action} no Confluence!\n{page_url}")

            published.add(sid)
            new_count += 1

        except Exception as e:
            log(f"ERRO ao publicar {name}: {e}")
            slack_notify(f"⚠️ sprint_confluence_watcher: erro ao publicar *{name}* — {e}")

    state["published_sprints"] = list(published)
    save_state(state)

    if new_count == 0:
        log("Nenhuma sprint nova para publicar.")
    else:
        log(f"{new_count} sprint(s) publicada(s).")

if __name__ == "__main__":
    main()
