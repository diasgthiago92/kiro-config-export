"""
Atlassian MCP Bridge (Jira + Confluence)
Protocolo: JSON-RPC 2.0 via stdin/stdout
Tools: jira_get_sprint_issues, jira_create_issue, jira_transition_issue,
       jira_assign_issue, jira_get_issue, jira_search, jira_sprint_report,
       jira_add_comment, confluence_search, confluence_get_page,
       confluence_create_page, confluence_update_page, confluence_list_pages
Dependência: pip install requests

[CONFIGURAR] Configure no .env:
  ATLASSIAN_URL=https://seu-dominio.atlassian.net
  ATLASSIAN_EMAIL=seu.email@empresa.com
  ATLASSIAN_TOKEN=seu_api_token
  JIRA_PROJECT=SUA_KEY
"""
import sys
import json
import os
import requests
from base64 import b64encode

def load_env():
    env_path = os.path.expanduser('~/Documents/Main/Brain/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

BASE_URL = os.getenv('ATLASSIAN_URL', 'https://seu-dominio.atlassian.net')
EMAIL = os.getenv('ATLASSIAN_EMAIL', '')
TOKEN = os.getenv('ATLASSIAN_TOKEN', '')
PROJECT = os.getenv('JIRA_PROJECT', 'PROJ')

def auth_header():
    creds = b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}

def jira_api(method, path, data=None):
    url = f"{BASE_URL}/rest/api/3/{path}"
    resp = requests.request(method, url, headers=auth_header(), json=data)
    return resp.json() if resp.content else {}

def confluence_api(method, path, data=None):
    url = f"{BASE_URL}/wiki/api/v2/{path}"
    resp = requests.request(method, url, headers=auth_header(), json=data)
    return resp.json() if resp.content else {}

# --- Tools Implementation ---
# Cada tool segue o padrão: recebe arguments, retorna string de resultado

def jira_search(jql, max_results=20):
    result = jira_api("GET", f"search?jql={jql}&maxResults={max_results}")
    issues = []
    for issue in result.get("issues", []):
        issues.append({
            "key": issue["key"],
            "summary": issue["fields"]["summary"],
            "status": issue["fields"]["status"]["name"],
            "type": issue["fields"]["issuetype"]["name"],
            "assignee": (issue["fields"].get("assignee") or {}).get("displayName")
        })
    return json.dumps(issues, ensure_ascii=False)

def jira_create_issue(summary, issue_type="Task", description="", labels=None):
    data = {
        "fields": {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {"type": "doc", "version": 1, "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": description or summary}]}
            ]},
            "labels": labels or []
        }
    }
    result = jira_api("POST", "issue", data)
    return json.dumps({"key": result.get("key"), "url": f"{BASE_URL}/browse/{result.get('key')}"})

# ... adicione as demais tools seguindo o mesmo padrão

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
            id_ = req.get("id")
            method = req.get("method")

            if method == "initialize":
                response = {"jsonrpc": "2.0", "id": id_, "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {"name": "atlassian-bridge", "version": "1.0.0"}
                }}
            elif method == "tools/list":
                response = {"jsonrpc": "2.0", "id": id_, "result": {"tools": [
                    {"name": "jira_search", "description": "Busca issues via JQL", "inputSchema": {
                        "type": "object",
                        "properties": {"jql": {"type": "string"}, "max_results": {"type": "integer", "default": 20}},
                        "required": ["jql"]
                    }},
                    {"name": "jira_create_issue", "description": "Cria uma issue no Jira", "inputSchema": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "issue_type": {"type": "string", "default": "Task"},
                            "description": {"type": "string"},
                            "labels": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["summary"]
                    }},
                    {"name": "jira_get_issue", "description": "Obtém detalhes de uma issue", "inputSchema": {
                        "type": "object",
                        "properties": {"issue_key": {"type": "string"}},
                        "required": ["issue_key"]
                    }},
                    {"name": "jira_transition_issue", "description": "Move issue para outro status", "inputSchema": {
                        "type": "object",
                        "properties": {"issue_key": {"type": "string"}, "transition_name": {"type": "string"}},
                        "required": ["issue_key", "transition_name"]
                    }},
                    # Adicione mais tools conforme necessário
                ]}}
            elif method == "tools/call":
                tool_name = req["params"]["name"]
                args = req["params"].get("arguments", {})
                
                if tool_name == "jira_search":
                    res_content = jira_search(args["jql"], args.get("max_results", 20))
                elif tool_name == "jira_create_issue":
                    res_content = jira_create_issue(
                        args["summary"],
                        args.get("issue_type", "Task"),
                        args.get("description", ""),
                        args.get("labels", [])
                    )
                elif tool_name == "jira_get_issue":
                    result = jira_api("GET", f"issue/{args['issue_key']}")
                    res_content = json.dumps({
                        "key": result["key"],
                        "summary": result["fields"]["summary"],
                        "status": result["fields"]["status"]["name"],
                        "type": result["fields"]["issuetype"]["name"]
                    }, ensure_ascii=False)
                else:
                    res_content = f"Tool '{tool_name}' não implementada ainda"
                
                response = {"jsonrpc": "2.0", "id": id_, "result": {
                    "content": [{"type": "text", "text": res_content}]
                }}
            else:
                response = {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found"}}

            print(json.dumps(response), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": id_, "error": {"message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()
