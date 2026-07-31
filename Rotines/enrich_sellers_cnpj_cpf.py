#!/usr/bin/env python3
"""
Enriquece a planilha SELLERS com CNPJ e CPF do Trino (ods.account).
- Lê account_ids da coluna A
- Consulta em grupos de 500
- Mantém o primeiro valor preenchido (sem sobrescrever)
- Escreve CNPJ na col B e CPF na col C
"""
import json
import subprocess
import time

SPREADSHEET_ID = "1J_JdlVt6zS8RAlV2fKgmy3bZUprlXYerRbvi4Q_gm6I"
SHEET_NAME = "SELLERS"
GOOGLE_BRIDGE = "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/google_bridge.py"
TRINO_BRIDGE = "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
BATCH_SIZE = 500


def google_call(tool, **args):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    })
    result = subprocess.run(
        ["python3", GOOGLE_BRIDGE],
        input=payload, capture_output=True, text=True
    )
    resp = json.loads(result.stdout)
    if "error" in resp:
        raise Exception(f"Google error: {resp['error']}")
    return json.loads(resp["result"]["content"][0]["text"])


def trino_query(sql):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "query", "arguments": {"sql": sql, "schema": "ods"}}
    })
    result = subprocess.run(
        ["python3", TRINO_BRIDGE],
        input=payload, capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data["result"]["content"][0]["text"]


def parse_trino_result(text):
    """Parse Trino result text into list of dicts."""
    import ast
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return []
    cols_line = next((l for l in lines if l.startswith("Colunas:")), None)
    dados_line = next((l for l in lines if l.startswith("Dados:")), None)
    if not cols_line or not dados_line:
        return []
    cols = ast.literal_eval(cols_line[len("Colunas: "):])
    rows = ast.literal_eval(dados_line[len("Dados: "):])
    return [dict(zip(cols, row)) for row in rows]


def main():
    print("Lendo planilha...")
    rows = google_call("sheets_read", spreadsheet_id=SPREADSHEET_ID, range_=f"{SHEET_NAME}!A:C")

    # rows[0] = header, rows[1:] = data
    header = rows[0]
    data_rows = rows[1:]
    total = len(data_rows)
    print(f"Total de linhas de dados: {total}")

    # Build map: account_id -> list of row indices (1-based, row 2 = index 0)
    # We need to track which rows already have CNPJ/CPF filled
    # For deduplication: keep first filled value per account_id
    # We'll collect all account_ids, query Trino, then fill only empty cells

    # Collect account_ids and their row positions
    account_rows = []  # list of (row_index_in_data, account_id, existing_cnpj, existing_cpf)
    for i, row in enumerate(data_rows):
        account_id = row[0].strip() if row else ""
        existing_cnpj = row[1].strip() if len(row) > 1 else ""
        existing_cpf = row[2].strip() if len(row) > 2 else ""
        if account_id:
            account_rows.append((i, account_id, existing_cnpj, existing_cpf))

    # Get unique account_ids that need lookup (missing CNPJ or CPF)
    ids_to_lookup = list({r[1] for r in account_rows if not r[2] or not r[3]})
    print(f"Account IDs únicos para buscar: {len(ids_to_lookup)}")

    # Query Trino in batches of 500
    # Use FIRST_VALUE to handle duplicates (keep first occurrence)
    trino_results = {}  # account_id -> {cnpj, cpf}

    for batch_start in range(0, len(ids_to_lookup), BATCH_SIZE):
        batch = ids_to_lookup[batch_start:batch_start + BATCH_SIZE]
        ids_str = ", ".join(batch)
        sql = f"""
            SELECT account_id_nk, cnpj, cpf
            FROM (
                SELECT
                    account_id_nk,
                    cnpj,
                    cpf,
                    ROW_NUMBER() OVER (PARTITION BY account_id_nk ORDER BY account_id_nk) AS rn
                FROM hive.ods.account
                WHERE account_id_nk IN ({ids_str})
                  AND (cnpj IS NOT NULL OR cpf IS NOT NULL)
            ) t
            WHERE rn = 1
        """
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(ids_to_lookup) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Consultando Trino: batch {batch_num}/{total_batches} ({len(batch)} IDs)...")

        result_text = trino_query(sql)
        rows_parsed = parse_trino_result(result_text)

        for r in rows_parsed:
            aid = str(r.get("account_id_nk", "")).strip()
            cnpj = str(r.get("cnpj", "") or "").strip()
            cpf = str(r.get("cpf", "") or "").strip()
            if aid:
                trino_results[aid] = {"cnpj": cnpj, "cpf": cpf}

        time.sleep(0.2)  # small delay between batches

    print(f"Resultados do Trino: {len(trino_results)} accounts encontrados")

    # Build update values for sheets_write
    # We write col B and C for all data rows
    # For rows where we have Trino data: use it (but don't overwrite existing)
    # For rows without data: leave empty string

    # Build the full B:C column values
    # sheets_write range: SELLERS!B2:C{total+1}
    update_values = []
    updated_count = 0

    for i, account_id, existing_cnpj, existing_cpf in account_rows:
        trino_data = trino_results.get(account_id, {})
        new_cnpj = existing_cnpj if existing_cnpj else trino_data.get("cnpj", "")
        new_cpf = existing_cpf if existing_cpf else trino_data.get("cpf", "")
        update_values.append([new_cnpj, new_cpf])
        if (not existing_cnpj and new_cnpj) or (not existing_cpf and new_cpf):
            updated_count += 1

    # Write only rows that have at least one new value, grouped into consecutive ranges
    rows_to_write = []  # list of (sheet_row_number, cnpj, cpf)
    for idx, (i, account_id, existing_cnpj, existing_cpf) in enumerate(account_rows):
        cnpj_val, cpf_val = update_values[idx]
        if cnpj_val or cpf_val:
            sheet_row = i + 2
            rows_to_write.append((sheet_row, cnpj_val, cpf_val))

    print(f"Escrevendo {len(rows_to_write)} linhas com dados na planilha ({updated_count} novas)...")

    # Group consecutive rows into batches for efficiency
    if rows_to_write:
        batch_start_idx = 0
        while batch_start_idx < len(rows_to_write):
            # Find consecutive run starting at batch_start_idx
            run = [rows_to_write[batch_start_idx]]
            j = batch_start_idx + 1
            while j < len(rows_to_write) and rows_to_write[j][0] == run[-1][0] + 1 and len(run) < 1000:
                run.append(rows_to_write[j])
                j += 1
            start_row = run[0][0]
            end_row = run[-1][0]
            values = [[r[1], r[2]] for r in run]
            range_str = f"{SHEET_NAME}!B{start_row}:C{end_row}"
            print(f"  Escrevendo linhas {start_row}-{end_row} ({len(run)} linhas)...")
            google_call("sheets_write", spreadsheet_id=SPREADSHEET_ID, range_=range_str, values=values)
            time.sleep(0.2)
            batch_start_idx = j

    print(f"\nConcluído! {updated_count} linhas atualizadas com CNPJ/CPF.")


if __name__ == "__main__":
    main()
