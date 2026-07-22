#!/usr/bin/env python3
"""
B3 — Atualização mensal do relatório de Financiamentos de Veículos
Verifica o site da B3, baixa novos relatórios e atualiza o knowledge base.
"""
import json, os, re, subprocess, sys, logging
from datetime import datetime
from pathlib import Path

BASE_URL = "https://www.b3.com.br"
PAGE_URL = f"{BASE_URL}/pt_br/market-data-e-indices/informacoes-para-mercado-de-financiamentos/veiculos/"
PDF_DIR  = Path.home() / "Documents/B3-Financiamentos-Veiculos/pdfs"
TXT_DIR  = Path.home() / "Documents/B3-Financiamentos-Veiculos/textos"
LOG_FILE = Path.home() / "b3_veiculos_updater.log"
SLACK_CHANNEL = "C0B2X8FQ81M"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger(__name__)


def slack_notify(msg: str):
    env_file = Path.home() / "Documents/Brain/.env"
    token = None
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("SLACK_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"')
    if not token:
        log.warning("SLACK_BOT_TOKEN não encontrado, pulando notificação")
        return
    payload = json.dumps({"channel": SLACK_CHANNEL, "text": msg})
    subprocess.run(
        ["curl", "-s", "-X", "POST", "https://slack.com/api/chat.postMessage",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {token}",
         "-d", payload],
        capture_output=True
    )


def fetch_page() -> str:
    r = subprocess.run(["curl", "-sL", PAGE_URL], capture_output=True, text=True)
    return r.stdout


def parse_pdf_links(html: str) -> dict:
    """Retorna dict {label: url} dos links de PDF encontrados na página."""
    pattern = r'href="(.*?\.pdf)"[^>]*>\s*(.*?)\s*<'
    links = {}
    for url, label in re.findall(pattern, html, re.IGNORECASE | re.DOTALL):
        label = re.sub(r'\s+', ' ', label).strip()
        if label:
            full_url = url if url.startswith("http") else BASE_URL + "/" + url.lstrip("/")
            links[label] = full_url
    return links


def extract_text(pdf_path: Path) -> str:
    import pypdf
    reader = pypdf.PdfReader(str(pdf_path))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def filename_from_url(url: str) -> str:
    """Gera nome de arquivo padronizado a partir da URL."""
    name = url.split("/")[-1]
    # Normaliza para b3_veiculos_MMMAA.pdf
    name = re.sub(r'Mercado%20de%20Financiamentos%20de%20Veiculos_?', '', name, flags=re.IGNORECASE)
    name = name.replace("%20", "_").lower()
    return f"b3_veiculos_{name}" if not name.startswith("b3_") else name


KNOWLEDGE_ID = "eb7e79b0-59cc-4730-a3d0-b3d4c5bf2eab"
KIRO_BIN = "/opt/homebrew/bin/kiro"

def update_knowledge_base():
    kiro = KIRO_BIN if os.path.exists(KIRO_BIN) else "kiro"
    subprocess.run(
        [kiro, "knowledge", "update", "--context-id", KNOWLEDGE_ID, str(TXT_DIR)],
        capture_output=True
    )


def main():
    log.info("=== Iniciando verificação B3 Veículos ===")

    html = fetch_page()
    if not html:
        msg = "❌ B3 Updater: falha ao acessar a página (VPN desconectada?)"
        log.error(msg)
        slack_notify(msg)
        sys.exit(1)

    links = parse_pdf_links(html)
    if not links:
        log.warning("Nenhum link de PDF encontrado na página")
        sys.exit(1)

    log.info(f"{len(links)} links encontrados na página")

    new_files = []
    for label, url in links.items():
        fname = filename_from_url(url)
        pdf_path = PDF_DIR / fname
        txt_path = TXT_DIR / fname.replace(".pdf", ".txt")

        if pdf_path.exists() and pdf_path.stat().st_size > 10_000:
            log.info(f"  skip {fname} (já existe)")
            continue

        log.info(f"  baixando {fname} ...")
        r = subprocess.run(["curl", "-sL", url, "-o", str(pdf_path)], capture_output=True)
        if not pdf_path.exists() or pdf_path.stat().st_size < 10_000:
            log.warning(f"  falha ao baixar {fname}")
            continue

        # Extrai texto
        try:
            text = f"# {fname.replace('b3_veiculos_','').replace('.pdf','').upper()} — Mercado de Financiamentos de Veículos B3\n\n"
            text += extract_text(pdf_path)
            txt_path.write_text(text)
            log.info(f"  ✓ {fname} ({len(text)//1000}KB de texto)")
            new_files.append(fname)
        except Exception as e:
            log.error(f"  erro ao extrair texto de {fname}: {e}")

    if new_files:
        log.info(f"Atualizando knowledge base com {len(new_files)} novo(s) arquivo(s)...")
        update_knowledge_base()
        msg = f"✅ *B3 Veículos atualizado* — {len(new_files)} novo(s) relatório(s) adicionado(s):\n" + \
              "\n".join(f"  • {f}" for f in new_files)
        slack_notify(msg)
        log.info("Knowledge base atualizado e Slack notificado.")
    else:
        log.info("Nenhum arquivo novo. Base já está atualizada.")

    log.info("=== Concluído ===")


if __name__ == "__main__":
    main()
