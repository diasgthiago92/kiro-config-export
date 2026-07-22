#!/usr/bin/env python3
"""
daily_support_report.py
Lê cards do board de suporte APRI (board 1364), categoriza por assunto
e publica relatório diário no Confluence > Suportes (7225475077).
Cron: 0 11 * * * /usr/bin/python3 /Users/thiago.dias/Documents/Main/Brain/Rotines/daily_support_report.py
"""

import json
import subprocess
from datetime import datetime
from collections import defaultdict

BRIDGE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/atlassian_bridge.py"
CONFLUENCE_PARENT_ID = "7225475077"
BOARD_ID = 1364
MAX_RESULTS = 100

# Categorias baseadas em palavras-chave no summary
CATEGORIES = {
    "Histórico Veicular (HV)": ["histórico veicular", "hv", "historico veicular", "renavam", "detran", "restrição", "estorno hv"],
    "Financiamento": ["financiamento", "financing", "proposta", "crédito", "credito", "safra", "santander"],
    "Anúncio / Publicação": ["anúncio", "anuncio", "publicação", "publicacao", "ad ", "listing"],
    "Pagamento / Cobrança": ["pagou", "pagamento", "cobrança", "cobranca", "estorno", "reembolso"],
    "Erro / Bug": ["erro", "error", "bug", "falha", "não funciona", "nao funciona", "problema"],
    "Acesso / Conta": ["acesso", "conta", "login", "senha", "bloqueio", "bloqueado"],
    "Outros": [],
}


def atlassian_call(tool, **args):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    })
    result = subprocess.run(
        ["python3", BRIDGE],
        input=payload, capture_output=True, text=True
    )
    return json.loads(json.loads(result.stdout)["result"]["content"][0]["text"])


def categorize(summary: str) -> str:
    text = summary.lower()
    for category, keywords in CATEGORIES.items():
        if category == "Outros":
            continue
        if any(kw in text for kw in keywords):
            return category
    return "Outros"


def fetch_all_issues():
    issues = []
    start = 0
    while True:
        data = atlassian_call(
            "jira_search",
            jql=f"project=APRI AND issuetype=Support ORDER BY created DESC",
            max_results=MAX_RESULTS
        )
        batch = data.get("issues", [])
        issues.extend(batch)
        if data.get("isLast", True) or len(batch) < MAX_RESULTS:
            break
        start += MAX_RESULTS
    return issues


def build_html(issues, today_str):
    by_status = defaultdict(list)
    by_category = defaultdict(list)

    for issue in issues:
        fields = issue["fields"]
        key = issue["key"]
        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "—")
        assignee = (fields.get("assignee") or {}).get("displayName", "Sem responsável")
        category = categorize(summary)
        link = f"https://olxbr.atlassian.net/browse/{key}"

        item = {"key": key, "summary": summary, "status": status, "assignee": assignee, "link": link}
        by_status[status].append(item)
        by_category[category].append(item)

    total = len(issues)
    open_statuses = {"Backlog", "Em andamento", "In Progress", "To Do", "Aberto"}
    total_open = sum(len(v) for k, v in by_status.items() if k in open_statuses)
    total_done = sum(len(v) for k, v in by_status.items() if k not in open_statuses)

    def issue_rows(items):
        rows = ""
        for i in items:
            rows += (
                f"<tr>"
                f"<td><a href='{i['link']}'>{i['key']}</a></td>"
                f"<td>{i['summary']}</td>"
                f"<td>{i['status']}</td>"
                f"<td>{i['assignee']}</td>"
                f"</tr>"
            )
        return rows

    # Resumo por status
    status_rows = "".join(
        f"<tr><td>{s}</td><td>{len(v)}</td></tr>"
        for s, v in sorted(by_status.items(), key=lambda x: -len(x[1]))
    )

    # Seções por categoria
    category_sections = ""
    for cat in CATEGORIES:
        items = by_category.get(cat, [])
        if not items:
            continue
        category_sections += f"""
        <h2>{cat} ({len(items)})</h2>
        <table>
          <thead><tr><th>Card</th><th>Resumo</th><th>Status</th><th>Responsável</th></tr></thead>
          <tbody>{issue_rows(items)}</tbody>
        </table>
        """

    html = f"""
    <h1>📋 Relatório Diário de Suportes — {today_str}</h1>

    <h2>Resumo Geral</h2>
    <table>
      <thead><tr><th>Métrica</th><th>Qtd</th></tr></thead>
      <tbody>
        <tr><td>Total de cards</td><td><strong>{total}</strong></td></tr>
        <tr><td>Em aberto</td><td><strong>{total_open}</strong></td></tr>
        <tr><td>Concluídos</td><td><strong>{total_done}</strong></td></tr>
      </tbody>
    </table>

    <h2>Por Status</h2>
    <table>
      <thead><tr><th>Status</th><th>Qtd</th></tr></thead>
      <tbody>{status_rows}</tbody>
    </table>

    {category_sections}

    <p><em>Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')} via daily_support_report.py</em></p>
    """
    return html


def main():
    today = datetime.now()
    today_str = today.strftime("%d/%m/%Y")
    page_title = f"Suporte Diário — {today.strftime('%Y-%m-%d')}"

    print(f"[{today_str}] Buscando cards do board de suporte APRI...")
    issues = fetch_all_issues()
    print(f"  {len(issues)} cards encontrados.")

    html = build_html(issues, today_str)

    # Verifica se já existe página para hoje
    search = atlassian_call("confluence_search", query=page_title, limit=5)
    existing = next((r for r in search.get("results", []) if r["title"] == page_title), None)

    if existing:
        print(f"  Atualizando página existente: {existing['id']}")
        atlassian_call("confluence_update_page", page_id=existing["id"], title=page_title, content_html=html)
    else:
        print(f"  Criando nova página no Confluence...")
        atlassian_call("confluence_create_page", title=page_title, content_html=html, parent_id=CONFLUENCE_PARENT_ID)

    print(f"  ✅ Relatório publicado: {page_title}")


if __name__ == "__main__":
    main()
