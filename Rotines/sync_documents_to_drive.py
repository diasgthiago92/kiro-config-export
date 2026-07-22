#!/usr/bin/env python3
"""
sync_documents_to_drive.py
Sincroniza ~/Documents para o Google Drive via rsync.
Roda todo dia às 17h via launchd.
"""
import subprocess, sys
from datetime import datetime
from pathlib import Path

SRC  = str(Path.home() / "Documents") + "/"
DEST = str(Path.home() / "Library/CloudStorage/GoogleDrive-thiago.dias@olxbr.com/Meu Drive/Backup_Thiago_Diario") + "/"

EXCLUDES = ["desktop.ini", ".DS_Store", "*.pyc", "__pycache__"]

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def main():
    cmd = ["rsync", "-av", "--delete"]
    for ex in EXCLUDES:
        cmd += ["--exclude", ex]
    cmd += [SRC, DEST]

    log(f"Iniciando sync: {SRC} → {DEST}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        lines = [l for l in result.stdout.splitlines() if l and not l.startswith("sending")]
        log(f"Sync concluído. {len(lines)} arquivo(s) processado(s).")
    else:
        log(f"ERRO no sync:\n{result.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()
