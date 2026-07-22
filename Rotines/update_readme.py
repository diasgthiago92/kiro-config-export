#!/usr/bin/env python3
"""
update_readme.py
Atualiza a data de "Última atualização" no README.md.
Roda toda sexta às 14h via launchd.
"""
import re
from datetime import datetime
from pathlib import Path

README = Path.home() / "Documents/Main/Brain/README.md"

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    content = README.read_text()
    content = re.sub(r"> Última atualização: .+", f"> Última atualização: {today}", content)
    README.write_text(content)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] README atualizado: {today}")

if __name__ == "__main__":
    main()
