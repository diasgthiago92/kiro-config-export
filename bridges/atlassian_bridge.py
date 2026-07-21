#!/usr/bin/env python3
"""MCP Bridge — Atlassian (Jira + Confluence) para o time APRI/APS1"""

import json
import os
import sys
from base64 import b64encode
from urllib import request, parse, error

# ── Config ────────────────────────────────────────────────────────────────────

def load_env():
    env_path = os.path.expanduser("~/Documents/Brain/.env")
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

ENV = load_env()
BASE_URL   = ENV["ATLASSIAN_URL"]
EMAIL      = ENV["ATLASSIAN_EMAIL"]
TOKEN      = ENV["ATLASSIAN_TOKEN"]
JIRA_PROJ  = ENV.get("JIRA_PROJECT", "APRI")
SPACE_KEY       = ENV.get("CONFLUENCE_SPACE", "APS1")
BOARD_ID        = int(ENV.get("JIRA_BOARD_ID", "1358"))
SPRINTS_PAGE_ID = ENV.get("CONFLUENCE_SPRINTS_PAGE_ID", "7214432314")  # VAS on the road > Sprints

AUTH_HEADER = "Basic " + b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()

# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _req(method, url, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Authorization": AUTH_HEADER, "Accept": "application/json",
                "Content-Type": "application/json"}
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req) as r:
            text = r.read().decode()
            return json.loads(text) if text else {}
    except error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode()}

def get(path, base="jira"):
    prefix = f"{BASE_URL}/rest/api/3" if base == "jira" else f"{BASE_URL}/wiki/rest/api"
    return _req("GET", prefix + path)

def agile(path):
    return _req("GET", f"{BASE_URL}/rest/agile/1.0" + path)

def post(path, body, base="jira"):
    prefix = f"{BASE_URL}/rest/api/3" if base == "jira" else f"{BASE_URL}/wiki/rest/api"
    return _req("POST", prefix + path, body)

def put(path, body, base="jira"):
    prefix = f"{BASE_URL}/rest/api/3" if base == "jira" else f"{BASE_URL}/wiki/rest/api"
    return _req("PUT", prefix + path, body)

# ── Jira tools ────────────────────────────────────────────────────────────────

def jira_get_sprint_issues(sprint_id=None, board_id=None):
    """Lista issues do sprint ativo ou de um sprint específico."""
    bid = board_id or BOARD_ID
    if sprint_id:
        sid = sprint_id
    else:
        sprints = agile(f"/board/{bid}/sprint?state=active")
        if not sprints.get("values"):
            return {"error": "Nenhum sprint ativo encontrado"}
        sid = sprints["values"][0]["id"]

    fields = "summary,status,assignee,issuetype,priority,story_points,customfield_10016"
    result = agile(f"/board/{bid}/sprint/{sid}/issue?maxResults=100&fields={fields}")
    issues = []
    for i in result.get("issues", []):
        f = i["fields"]
        issues.append({
            "key": i["key"],
            "type": f["issuetype"]["name"],
            "status": f["status"]["name"],
            "assignee": f.get("assignee", {}).get("displayName") if f.get("assignee") else None,
            "summary": f["summary"],
            "points": f.get("customfield_10016"),
        })
    return {"sprint_id": sid, "total": len(issues), "issues": issues}

QUARTER_IDS = {
    "Q12026": "21444", "Q22026": "22915", "Q32026": "22916",
    "Q42026": "22917", "Não Planejado": "23302",
}
CLASSIFICACAO_IDS = {"Mapa Estratégico": "23198", "BAU": "23199"}
STACK_IDS = {
    "Analytics Engineering": "20689", "Android": "12335", "Backend": "12336",
    "Data Analytics": "12337", "Data Science": "12368", "Frontend": "12338",
    "iOS": "12339", "Product Analytics": "20690",
}

def jira_create_issue(summary, issue_type="História", description=None, assignee_email=None,
                      priority="Medium", labels=None, quarter="Não Planejado", classificacao="BAU",
                      stacks=None, criterios_aceite=None):
    """Cria uma issue no projeto APRI.
    quarter: Q12026 | Q22026 | Q32026 | Q42026 | Não Planejado
    classificacao: Mapa Estratégico | BAU
    stacks: lista de stacks ex: ["Frontend", "Backend"]
    criterios_aceite: texto com os critérios de aceite
    """
    body = {
        "fields": {
            "project": {"key": JIRA_PROJ},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "customfield_10587": [{"id": QUARTER_IDS.get(quarter, "23302")}],
            "customfield_13309": {"id": CLASSIFICACAO_IDS.get(classificacao, "23199")},
        }
    }
    if stacks:
        stack_list = stacks if isinstance(stacks, list) else [stacks]
        body["fields"]["customfield_10983"] = [{"id": STACK_IDS[s]} for s in stack_list if s in STACK_IDS]
    if criterios_aceite:
        body["fields"]["customfield_13310"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": criterios_aceite}]}]
        }
    if description:
        body["fields"]["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
        }
    if assignee_email:
        users = get(f"/user/search?query={parse.quote(assignee_email)}")
        if users and not isinstance(users, dict):
            body["fields"]["assignee"] = {"accountId": users[0]["accountId"]}
    if labels:
        body["fields"]["labels"] = labels if isinstance(labels, list) else [labels]

    return post("/issue", body)

def jira_transition_issue(issue_key, transition_name):
    """Move uma issue para um novo status pelo nome da transição."""
    transitions = get(f"/issue/{issue_key}/transitions")
    name_map = {t["name"].lower(): t["id"] for t in transitions.get("transitions", [])}
    tid = name_map.get(transition_name.lower())
    if not tid:
        return {"error": f"Transição '{transition_name}' não encontrada", "available": list(name_map.keys())}
    return post(f"/issue/{issue_key}/transitions", {"transition": {"id": tid}})

def jira_assign_issue(issue_key, assignee_email):
    """Atribui uma issue a um membro do time."""
    users = get(f"/user/search?query={parse.quote(assignee_email)}")
    if not users or isinstance(users, dict):
        return {"error": f"Usuário '{assignee_email}' não encontrado"}
    account_id = users[0]["accountId"]
    return put(f"/issue/{issue_key}/assignee", {"accountId": account_id})

def jira_get_issue(issue_key):
    """Retorna detalhes de uma issue."""
    return get(f"/issue/{issue_key}?fields=summary,status,assignee,issuetype,description,priority,comment,customfield_10016")

def jira_search(jql, max_results=50):
    """Busca issues via JQL."""
    return _req("POST", f"{BASE_URL}/rest/api/3/search/jql", {
        "jql": jql, "maxResults": max_results,
        "fields": ["summary", "status", "assignee", "issuetype", "priority"]
    })

def jira_sprint_report(board_id=None):
    """Gera relatório do sprint ativo: concluídos, em andamento, não iniciados."""
    bid = board_id or BOARD_ID
    sprints = agile(f"/board/{bid}/sprint?state=active")
    if not sprints.get("values"):
        return {"error": "Nenhum sprint ativo"}
    sprint = sprints["values"][0]
    data = jira_get_sprint_issues(sprint["id"], bid)

    report = {"sprint": sprint["name"], "start": sprint.get("startDate","")[:10],
              "end": sprint.get("endDate","")[:10], "total": data["total"],
              "done": [], "in_progress": [], "todo": [], "review": []}

    for i in data["issues"]:
        s = i["status"].lower()
        if "conclu" in s or "done" in s:
            report["done"].append(i)
        elif "andamento" in s or "progress" in s:
            report["in_progress"].append(i)
        elif "review" in s:
            report["review"].append(i)
        else:
            report["todo"].append(i)

    report["summary"] = {
        "done": len(report["done"]),
        "in_progress": len(report["in_progress"]),
        "review": len(report["review"]),
        "todo": len(report["todo"]),
    }
    return report

def jira_add_comment(issue_key, comment_text):
    """Adiciona comentário em uma issue."""
    body = {
        "body": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment_text}]}]
        }
    }
    return post(f"/issue/{issue_key}/comment", body)

# ── Confluence tools ──────────────────────────────────────────────────────────

def confluence_search(query, limit=10):
    """Busca páginas no espaço APS1."""
    encoded = parse.quote(f'space="{SPACE_KEY}" AND text~"{query}"')
    return get(f"/content/search?cql={encoded}&limit={limit}", base="confluence")

def confluence_get_page(page_id):
    """Retorna conteúdo de uma página."""
    return get(f"/content/{page_id}?expand=body.storage,version", base="confluence")

def confluence_create_page(title, content_html, parent_id=None):
    """Cria uma nova página no espaço APS1."""
    body = {
        "type": "page",
        "title": title,
        "space": {"key": SPACE_KEY},
        "body": {"storage": {"value": content_html, "representation": "storage"}},
    }
    if parent_id:
        body["ancestors"] = [{"id": str(parent_id)}]
    return post("/content", body, base="confluence")

def confluence_update_page(page_id, title, content_html):
    """Atualiza o conteúdo de uma página existente."""
    current = confluence_get_page(page_id)
    if "error" in current:
        return current
    version = current["version"]["number"] + 1
    body = {
        "type": "page",
        "title": title,
        "version": {"number": version},
        "body": {"storage": {"value": content_html, "representation": "storage"}},
    }
    return put(f"/content/{page_id}", body, base="confluence")

def confluence_list_pages(parent_id=None, limit=25):
    """Lista páginas do espaço APS1."""
    if parent_id:
        path = f"/content/{parent_id}/child/page?limit={limit}"
    else:
        path = f"/content?spaceKey={SPACE_KEY}&type=page&limit={limit}"
    return get(path, base="confluence")

def confluence_publish_sprint_report():
    """Cria/atualiza página de relatório do sprint ativo no Confluence."""
    report = jira_sprint_report()
    if "error" in report:
        return report

    rows_done = "".join(f"<tr><td>{i['key']}</td><td>{i['summary']}</td><td>{i.get('assignee','—')}</td></tr>" for i in report["done"])
    rows_wip  = "".join(f"<tr><td>{i['key']}</td><td>{i['summary']}</td><td>{i.get('assignee','—')}</td></tr>" for i in report["in_progress"])
    rows_rev  = "".join(f"<tr><td>{i['key']}</td><td>{i['summary']}</td><td>{i.get('assignee','—')}</td></tr>" for i in report["review"])
    rows_todo = "".join(f"<tr><td>{i['key']}</td><td>{i['summary']}</td><td>{i.get('assignee','—')}</td></tr>" for i in report["todo"])

    def table(rows, label):
        if not rows:
            return f"<h3>{label} (0)</h3><p>Nenhuma issue.</p>"
        return f"""<h3>{label}</h3>
<table><tbody>
<tr><th>Key</th><th>Resumo</th><th>Responsável</th></tr>
{rows}
</tbody></table>"""

    html = f"""<h1>Relatório: {report['sprint']}</h1>
<p><strong>Período:</strong> {report['start']} → {report['end']}</p>
<p><strong>Total:</strong> {report['total']} issues |
✅ Concluídas: {report['summary']['done']} |
🔄 Em andamento: {report['summary']['in_progress']} |
👀 Code Review: {report['summary']['review']} |
📋 A fazer: {report['summary']['todo']}</p>
{table(rows_done, '✅ Concluídas')}
{table(rows_wip, '🔄 Em Andamento')}
{table(rows_rev, '👀 Code Review')}
{table(rows_todo, '📋 A Fazer')}"""

    title = f"Sprint Report — {report['sprint']}"

    # Verifica se já existe dentro da pasta Sprints
    children = get(f"/content/{SPRINTS_PAGE_ID}/child/page?limit=50", base="confluence")
    for page in children.get("results", []):
        if page["title"] == title:
            return confluence_update_page(page["id"], title, html)

    return confluence_create_page(title, html, parent_id=SPRINTS_PAGE_ID)

# ── MCP dispatcher ────────────────────────────────────────────────────────────

TOOLS = {
    # Jira
    "jira_get_sprint_issues":    jira_get_sprint_issues,
    "jira_create_issue":         jira_create_issue,
    "jira_transition_issue":     jira_transition_issue,
    "jira_assign_issue":         jira_assign_issue,
    "jira_get_issue":            jira_get_issue,
    "jira_search":               jira_search,
    "jira_sprint_report":        jira_sprint_report,
    "jira_add_comment":          jira_add_comment,
    # Confluence
    "confluence_search":         confluence_search,
    "confluence_get_page":       confluence_get_page,
    "confluence_create_page":    confluence_create_page,
    "confluence_update_page":    confluence_update_page,
    "confluence_list_pages":     confluence_list_pages,
    "confluence_publish_sprint_report": confluence_publish_sprint_report,
}

def handle(payload):
    method = payload.get("method")
    pid    = payload.get("id", 1)

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": pid, "result": {"tools": [{"name": k} for k in TOOLS]}}

    if method == "tools/call":
        name = payload["params"]["name"]
        args = payload["params"].get("arguments", {})
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": pid, "error": {"message": f"Tool '{name}' not found"}}
        try:
            result = TOOLS[name](**args)
            return {"jsonrpc": "2.0", "id": pid, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": pid, "error": {"message": str(e)}}

    return {"jsonrpc": "2.0", "id": pid, "error": {"message": f"Unknown method: {method}"}}

if __name__ == "__main__":
    raw = sys.stdin.read()
    payload = json.loads(raw)
    print(json.dumps(handle(payload), ensure_ascii=False))
