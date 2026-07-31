#!/usr/bin/env python3
"""Googlinho — Agente CLI para Google Drive, Sheets, Slides e Gmail"""

import json
import subprocess
import sys

BRIDGE = "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/google_bridge.py"

def call(tool, **args):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    })
    result = subprocess.run(
        ["python3", BRIDGE], input=payload, capture_output=True, text=True
    )
    if result.returncode != 0:
        return {"error": result.stderr}
    data = json.loads(result.stdout)
    if "error" in data:
        return data["error"]
    return json.loads(data["result"]["content"][0]["text"])

def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def cmd_drive_list(args):
    query = " ".join(args) if args else None
    files = call("drive_list", query=query, max_results=20)
    if isinstance(files, list):
        for f in files:
            print(f"📄 {f['name']} ({f['mimeType'].split('.')[-1]}) — {f.get('webViewLink','')}")
    else:
        print_json(files)

def cmd_drive_search(args):
    if not args:
        print("Uso: drive-search <nome>")
        return
    files = call("drive_search", name=" ".join(args))
    if isinstance(files, list):
        for f in files:
            print(f"📄 {f['name']} — {f.get('webViewLink','')}")
    else:
        print_json(files)

def cmd_sheets_read(args):
    if len(args) < 2:
        print("Uso: sheets-read <spreadsheet_id> <range>")
        return
    rows = call("sheets_read", spreadsheet_id=args[0], range_=args[1])
    if isinstance(rows, list):
        for row in rows:
            print("\t".join(str(c) for c in row))
    else:
        print_json(rows)

def cmd_sheets_write(args):
    if len(args) < 3:
        print("Uso: sheets-write <spreadsheet_id> <range> <json_values>")
        return
    values = json.loads(args[2])
    print_json(call("sheets_write", spreadsheet_id=args[0], range_=args[1], values=values))

def cmd_sheets_append(args):
    if len(args) < 3:
        print("Uso: sheets-append <spreadsheet_id> <range> <json_values>")
        return
    values = json.loads(args[2])
    print_json(call("sheets_append", spreadsheet_id=args[0], range_=args[1], values=values))

def cmd_sheets_info(args):
    if not args:
        print("Uso: sheets-info <spreadsheet_id>")
        return
    print_json(call("sheets_get_info", spreadsheet_id=args[0]))

def cmd_slides_get(args):
    if not args:
        print("Uso: slides-get <presentation_id>")
        return
    data = call("slides_get", presentation_id=args[0])
    if isinstance(data, dict) and "slides" in data:
        print(f"📊 {data['title']} — {len(data['slides'])} slides")
        for s in data["slides"]:
            print(f"  Slide {s['slide']}: {' | '.join(s['texts'][:3])}")
    else:
        print_json(data)

def cmd_gmail_list(args):
    query = " ".join(args) if args else ""
    msgs = call("gmail_list", max_results=10, query=query)
    if isinstance(msgs, list):
        for m in msgs:
            print(f"📧 [{m['id'][:8]}] {m['subject']} — {m['from']} ({m['date'][:16]})")
    else:
        print_json(msgs)

def cmd_gmail_read(args):
    if not args:
        print("Uso: gmail-read <message_id>")
        return
    msg = call("gmail_read", message_id=args[0])
    if isinstance(msg, dict):
        print(f"De: {msg['from']}")
        print(f"Para: {msg['to']}")
        print(f"Assunto: {msg['subject']}")
        print(f"Data: {msg['date']}")
        print("─" * 60)
        print(msg.get("body", "")[:2000])
    else:
        print_json(msg)

def cmd_gmail_send(args):
    if len(args) < 3:
        print("Uso: gmail-send <para> <assunto> <corpo>")
        return
    result = call("gmail_send", to=args[0], subject=args[1], body=" ".join(args[2:]))
    print(f"✅ E-mail enviado! ID: {result.get('id','?')}" if isinstance(result, dict) and "id" in result else print_json(result))

def cmd_gmail_search(args):
    if not args:
        print("Uso: gmail-search <query>")
        return
    msgs = call("gmail_search", query=" ".join(args))
    if isinstance(msgs, list):
        for m in msgs:
            print(f"📧 [{m['id'][:8]}] {m['subject']} — {m['from']}")
    else:
        print_json(msgs)

COMMANDS = {
    "drive-list":     cmd_drive_list,
    "drive-search":   cmd_drive_search,
    "sheets-read":    cmd_sheets_read,
    "sheets-write":   cmd_sheets_write,
    "sheets-append":  cmd_sheets_append,
    "sheets-info":    cmd_sheets_info,
    "slides-get":     cmd_slides_get,
    "gmail-list":     cmd_gmail_list,
    "gmail-read":     cmd_gmail_read,
    "gmail-send":     cmd_gmail_send,
    "gmail-search":   cmd_gmail_search,
}

HELP = """
Googlinho — Google Drive, Sheets, Slides e Gmail

Drive:
  drive-list [query]                     Lista arquivos no Drive
  drive-search <nome>                    Busca arquivos por nome

Sheets:
  sheets-read <id> <range>               Lê células (ex: Sheet1!A1:D10)
  sheets-write <id> <range> <json>       Escreve valores
  sheets-append <id> <range> <json>      Adiciona linhas
  sheets-info <id>                       Metadados e abas da planilha

Slides:
  slides-get <id>                        Lê estrutura da apresentação

Gmail:
  gmail-list [query]                     Lista e-mails da inbox
  gmail-read <id>                        Lê e-mail completo
  gmail-send <para> <assunto> <corpo>    Envia e-mail
  gmail-search <query>                   Busca e-mails
"""

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(HELP)
        sys.exit(0)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd not in COMMANDS:
        print(f"Comando desconhecido: {cmd}\n{HELP}")
        sys.exit(1)

    COMMANDS[cmd](rest)
