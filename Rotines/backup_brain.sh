#!/bin/bash
BRAIN="/Users/[YOUR_USER]/Documents/Main/Brain"
DEST="/Users/[YOUR_USER]/Documents/Brain-Backup/backup_$(date +%Y-%m-%d_%H-%M)"
mkdir -p "$DEST"

cp -R "$BRAIN/Bridges" "$DEST/" 2>/dev/null
cp -R "$BRAIN/Agents" "$DEST/" 2>/dev/null
cp -R "$BRAIN/Prompts" "$DEST/" 2>/dev/null
cp -R "$BRAIN/Rotines" "$DEST/" 2>/dev/null
cp "$BRAIN/.env" "$DEST/" 2>/dev/null

echo "[$(date)] Backup concluído em $DEST"
