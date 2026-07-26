#!/usr/bin/env python3
"""MCP Bridge — Google (Drive, Sheets, Slides, Gmail)"""

import json
import os
import sys
import base64
import email as email_lib
from email.mime.text import MIMEText

# ── Auth ──────────────────────────────────────────────────────────────────────

def load_env():
    for path in ["~/Documents/Main/Brain/.env", "~/Documents/Brain/.env"]:
        p = os.path.expanduser(path)
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())

load_env()

SA_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
]
GMAIL_SCOPES = OAUTH_SCOPES  # alias para compatibilidade

def get_sa_credentials():
    """Service Account — Drive, Sheets, Slides."""
    from google.oauth2 import service_account
    key_path = os.path.expanduser("~/.kiro/google_service_account.json")
    return service_account.Credentials.from_service_account_file(key_path, scopes=SA_SCOPES)

def get_gmail_credentials():
    """OAuth2 — Gmail (requer ~/.kiro/google_credentials.json na primeira execução)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = os.path.expanduser("~/.kiro/google_token.json")
    creds_path = os.path.expanduser("~/.kiro/google_credentials.json")
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return creds

def build_service(name, version):
    from googleapiclient.discovery import build
    creds = get_gmail_credentials() if name in ("gmail", "slides") else get_sa_credentials()
    return build(name, version, credentials=creds)

# ── Drive ─────────────────────────────────────────────────────────────────────

def drive_list(query=None, max_results=20):
    """Lista arquivos no Google Drive."""
    svc = build_service("drive", "v3")
    q = query or ""
    res = svc.files().list(
        q=q, pageSize=max_results,
        fields="files(id,name,mimeType,modifiedTime,webViewLink)"
    ).execute()
    return res.get("files", [])

def drive_search(name, max_results=10):
    """Busca arquivos por nome no Drive."""
    return drive_list(query=f"name contains '{name}' and trashed=false", max_results=max_results)

def drive_get_file(file_id):
    """Retorna metadados de um arquivo."""
    svc = build_service("drive", "v3")
    return svc.files().get(
        fileId=file_id,
        fields="id,name,mimeType,modifiedTime,webViewLink,parents"
    ).execute()

def drive_create_folder(name, parent_id=None):
    """Cria uma pasta no Drive."""
    svc = build_service("drive", "v3")
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    return svc.files().create(body=meta, fields="id,name,webViewLink").execute()

# ── Sheets ────────────────────────────────────────────────────────────────────

def sheets_read(spreadsheet_id, range_):
    """Lê valores de um intervalo da planilha."""
    svc = build_service("sheets", "v4")
    res = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_
    ).execute()
    return res.get("values", [])

def sheets_write(spreadsheet_id, range_, values):
    """Escreve valores em um intervalo da planilha."""
    svc = build_service("sheets", "v4")
    body = {"values": values}
    return svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_,
        valueInputOption="USER_ENTERED", body=body
    ).execute()

def sheets_append(spreadsheet_id, range_, values):
    """Adiciona linhas ao final de um intervalo."""
    svc = build_service("sheets", "v4")
    body = {"values": values}
    return svc.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=range_,
        valueInputOption="USER_ENTERED", body=body
    ).execute()

def sheets_create(title):
    """Cria uma nova planilha."""
    svc = build_service("sheets", "v4")
    return svc.spreadsheets().create(body={"properties": {"title": title}}).execute()

def sheets_get_info(spreadsheet_id):
    """Retorna metadados e abas da planilha."""
    svc = build_service("sheets", "v4")
    res = svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return {
        "title": res["properties"]["title"],
        "sheets": [s["properties"]["title"] for s in res.get("sheets", [])],
        "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    }

# ── Slides ────────────────────────────────────────────────────────────────────

def slides_get(presentation_id):
    """Retorna estrutura de uma apresentação."""
    svc = build_service("slides", "v1")
    pres = svc.presentations().get(presentationId=presentation_id).execute()
    slides = []
    for i, slide in enumerate(pres.get("slides", []), 1):
        texts = []
        for el in slide.get("pageElements", []):
            shape = el.get("shape", {})
            text_content = shape.get("text", {})
            for run in text_content.get("textElements", []):
                t = run.get("textRun", {}).get("content", "").strip()
                if t:
                    texts.append(t)
        slides.append({"slide": i, "id": slide["objectId"], "texts": texts})
    return {"title": pres["title"], "slides": slides}

def slides_create(title):
    """Cria uma nova apresentação."""
    svc = build_service("slides", "v1")
    return svc.presentations().create(body={"title": title}).execute()

def slides_add_text_slide(presentation_id, title_text, body_text):
    """Adiciona um slide com título e corpo de texto."""
    svc = build_service("slides", "v1")
    # Adiciona slide em branco
    add_req = [{"createSlide": {"slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"}}}]
    res = svc.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": add_req}
    ).execute()
    slide_id = res["replies"][0]["createSlide"]["objectId"]

    # Busca IDs dos placeholders
    pres = svc.presentations().get(presentationId=presentation_id).execute()
    slide = next(s for s in pres["slides"] if s["objectId"] == slide_id)
    title_id = body_id = None
    for el in slide.get("pageElements", []):
        ph = el.get("shape", {}).get("placeholder", {})
        if ph.get("type") == "TITLE":
            title_id = el["objectId"]
        elif ph.get("type") == "BODY":
            body_id = el["objectId"]

    requests = []
    if title_id:
        requests.append({"insertText": {"objectId": title_id, "text": title_text}})
    if body_id:
        requests.append({"insertText": {"objectId": body_id, "text": body_text}})

    if requests:
        svc.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": requests}
        ).execute()

    return {"slide_id": slide_id, "presentation_id": presentation_id}

# ── Gmail ─────────────────────────────────────────────────────────────────────

def gmail_list(max_results=10, query=""):
    """Lista e-mails da caixa de entrada."""
    svc = build_service("gmail", "v1")
    q = query or "in:inbox"
    res = svc.users().messages().list(userId="me", q=q, maxResults=max_results).execute()
    messages = []
    for msg in res.get("messages", []):
        m = svc.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in m["payload"].get("headers", [])}
        messages.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": m.get("snippet", ""),
        })
    return messages

def gmail_read(message_id):
    """Lê o conteúdo completo de um e-mail."""
    svc = build_service("gmail", "v1")
    m = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in m["payload"].get("headers", [])}

    def extract_body(payload):
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            if part["mimeType"] in ("text/plain", "text/html"):
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return ""

    return {
        "id": message_id,
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "body": extract_body(m["payload"]),
    }

def gmail_send(to, subject, body, reply_to_id=None):
    """Envia um e-mail."""
    svc = build_service("gmail", "v1")
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = {"raw": raw}
    if reply_to_id:
        payload["threadId"] = reply_to_id
    return svc.users().messages().send(userId="me", body=payload).execute()

def gmail_search(query, max_results=10):
    """Busca e-mails por query (ex: 'from:alguem@gmail.com subject:reunião')."""
    return gmail_list(max_results=max_results, query=query)

def gmail_mark_read(message_id):
    """Marca um e-mail como lido."""
    svc = build_service("gmail", "v1")
    return svc.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()

# ── MCP dispatcher ────────────────────────────────────────────────────────────

TOOLS = {
    # Drive
    "drive_list":          drive_list,
    "drive_search":        drive_search,
    "drive_get_file":      drive_get_file,
    "drive_create_folder": drive_create_folder,
    # Sheets
    "sheets_read":         sheets_read,
    "sheets_write":        sheets_write,
    "sheets_append":       sheets_append,
    "sheets_create":       sheets_create,
    "sheets_get_info":     sheets_get_info,
    # Slides
    "slides_get":          slides_get,
    "slides_create":       slides_create,
    "slides_add_text_slide": slides_add_text_slide,
    # Gmail
    "gmail_list":          gmail_list,
    "gmail_read":          gmail_read,
    "gmail_send":          gmail_send,
    "gmail_search":        gmail_search,
    "gmail_mark_read":     gmail_mark_read,
}

def handle(payload):
    method = payload.get("method")
    pid = payload.get("id", 1)

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": pid, "result": {"tools": [{"name": k} for k in TOOLS]}}

    if method == "tools/call":
        name = payload["params"]["name"]
        args = payload["params"].get("arguments", {})
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": pid, "error": {"message": f"Tool '{name}' not found"}}
        try:
            result = TOOLS[name](**args)
            return {"jsonrpc": "2.0", "id": pid, "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
            }}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": pid, "error": {"message": str(e)}}

    return {"jsonrpc": "2.0", "id": pid, "error": {"message": f"Unknown method: {method}"}}

if __name__ == "__main__":
    raw = sys.stdin.read()
    payload = json.loads(raw)
    print(json.dumps(handle(payload), ensure_ascii=False))
