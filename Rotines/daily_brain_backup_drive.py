#!/usr/bin/env python3
"""
Rotina: Backup diário da pasta Brain para o Google Drive.
Cron: 0 10 30 * * * /usr/bin/python3 /Users/[YOUR_USER]/Documents/Main/Brain/Rotines/daily_brain_backup_drive.py
Destino: Backup_Thiago_Diario (1fl2LUzX31qHAf62zL82l4ZIIZ4CuuZQV)
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ─── Config ────────────────────────────────────────────────────────────────────
BRAIN_DIR = Path.home() / "Documents/Main/Brain"
SA_FILE = Path.home() / ".kiro/google_service_account.json"
DRIVE_PARENT_FOLDER_ID = "1fl2LUzX31qHAf62zL82l4ZIIZ4CuuZQV"  # Backup_Thiago_Diario
SLACK_BRIDGE = str(BRAIN_DIR / "Bridges/slack_bridge.py")
SLACK_CHANNEL = "C0B2X8FQ81M"
SCOPES = ["https://www.googleapis.com/auth/drive"]

# ─── Helpers ───────────────────────────────────────────────────────────────────

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(str(SA_FILE), scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def create_folder(service, name, parent_id):
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(
        body=metadata, supportsAllDrives=True, fields="id,name"
    ).execute()
    return folder["id"]


def upload_file(service, local_path, parent_id, retries=3):
    # Resolve symlinks
    real_path = local_path.resolve()
    if not real_path.exists():
        print(f"  ⚠️  Skipping (broken link): {local_path.name}")
        return

    mime = "application/octet-stream"
    ext = real_path.suffix.lower()
    mime_map = {
        ".py": "text/x-python",
        ".md": "text/markdown",
        ".sh": "text/x-shellscript",
        ".txt": "text/plain",
        ".json": "application/json",
        ".env": "text/plain",
    }
    mime = mime_map.get(ext, mime)

    metadata = {"name": local_path.name, "parents": [parent_id]}
    media = MediaFileUpload(str(real_path), mimetype=mime, resumable=True)

    import time
    for attempt in range(retries):
        try:
            service.files().create(
                body=metadata, media_body=media, supportsAllDrives=True, fields="id"
            ).execute()
            return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  ❌ Failed to upload {local_path.name}: {e}")
                raise


def upload_directory(service, local_dir, drive_parent_id):
    """Recursively upload a directory to Google Drive."""
    for item in sorted(local_dir.iterdir()):
        if item.name.startswith(".") and item.name != ".env":
            continue
        if item.is_dir():
            subfolder_id = create_folder(service, item.name, drive_parent_id)
            upload_directory(service, item, subfolder_id)
        elif item.is_file() or item.is_symlink():
            upload_file(service, item, drive_parent_id)


def notify_slack(message):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {
            "name": "send_message",
            "arguments": {"channel": SLACK_CHANNEL, "text": message}
        }
    })
    subprocess.run(
        ["python3", SLACK_BRIDGE],
        input=payload, capture_output=True, text=True
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[{datetime.now()}] Iniciando backup Brain → Drive ({today})")

    try:
        service = get_drive_service()

        # Criar pasta do dia dentro de Backup_Thiago_Diario
        day_folder_id = create_folder(service, f"Brain_{today}", DRIVE_PARENT_FOLDER_ID)

        # Upload recursivo
        upload_directory(service, BRAIN_DIR, day_folder_id)

        msg = f"✅ Backup Brain → Drive concluído ({today})"
        print(f"[{datetime.now()}] {msg}")
        notify_slack(msg)

    except Exception as e:
        msg = f"❌ Falha no backup Brain → Drive ({today}): {e}"
        print(f"[{datetime.now()}] {msg}")
        notify_slack(msg)
        raise


if __name__ == "__main__":
    main()
