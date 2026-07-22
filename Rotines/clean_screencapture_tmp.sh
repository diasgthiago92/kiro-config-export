#!/bin/bash
SRC="/var/folders/j2/mmykdw6d3jjfm34tp9ngzg7c0000gn/T/TemporaryItems/NSIRD_screencaptureui_Mp7tFx"
TRASH="$HOME/.Trash"

find "$SRC" -maxdepth 1 -type f -name "*.png" -exec mv -f {} "$TRASH/" \;
