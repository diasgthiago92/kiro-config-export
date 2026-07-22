#!/usr/bin/env python3
"""
Busca CNPJ e CPF na ods.account para cada account_id da planilha SELLERS.
- Consulta Trino em batches de 500
- Para duplicatas de account_id: mantém o valor não nulo
- Escreve APENAS nas linhas com resultado (não sobrescreve com vazio)
"""
import json, subprocess, ast, time

SPREADSHEET_ID = "1J_JdlVt6zS8RAlV2fKgmy3bZUprlXYerRbvi4Q_gm6I"
SHEET = "SELLERS"
GOOGLE_BRIDGE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/google_bridge.py"
TRINO_BRIDGE  = "/Users/thiago.dias/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
BATCH = 500

def google(tool, **args):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}})
    r = subprocess.run(["python3", GOOGLE_BRIDGE], input=payload, capture_output=True, text=True)
    resp = json.loads(r.stdout)
    if "error" in resp:
        raise Exception(resp["error"])
    return json.loads(resp["result"]["content"][0]["text"])

def trino(sql):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"query","arguments":{"sql":sql,"schema":"ods"}}})
    r = subprocess.run(["python3", TRINO_BRIDGE], input=payload, capture_output=True, text=True)
    text = json.loads(r.stdout)["result"]["content"][0]["text"]
    lines = text.strip().split("\n")
    cols = ast.literal_eval(next(l[len("Colunas: "):] for l in lines if l.startswith("Colunas:")))
    rows = ast.literal_eval(next(l[len("Dados: "):] for l in lines if l.startswith("Dados:")))
    return [dict(zip(cols, row)) for row in rows]

# 1. Ler todos os account_ids
print("Lendo planilha...")
all_rows = google("sheets_read", spreadsheet_id=SPREADSHEET_ID, range_=f"{SHEET}!A:A")
# all_rows[0] = header
account_ids = [r[0].strip() for r in all_rows[1:] if r and r[0].strip()]
total = len(account_ids)
print(f"Total de linhas: {total}")

# 2. Unique IDs para consultar
unique_ids = list(set(account_ids))
print(f"IDs únicos: {len(unique_ids)}")

# 3. Consultar Trino em batches — mantém valor não nulo para duplicatas
results = {}  # account_id_str -> {cnpj, cpf}

for i in range(0, len(unique_ids), BATCH):
    batch = unique_ids[i:i+BATCH]
    batch_n = i // BATCH + 1
    total_batches = (len(unique_ids) + BATCH - 1) // BATCH
    print(f"Trino batch {batch_n}/{total_batches}...")
    ids_str = ", ".join(batch)
    sql = f"""
        SELECT account_id_nk,
               MAX(cnpj) AS cnpj,
               MAX(cpf)  AS cpf
        FROM hive.ods.account
        WHERE account_id_nk IN ({ids_str})
        GROUP BY account_id_nk
    """
    for row in trino(sql):
        aid = str(row["account_id_nk"])
        cnpj = str(row["cnpj"] or "").strip()
        cpf  = str(row["cpf"]  or "").strip()
        if cnpj or cpf:
            results[aid] = {"cnpj": cnpj, "cpf": cpf}
    time.sleep(0.1)

print(f"Encontrados no Trino: {len(results)} IDs com CNPJ ou CPF")

# 4. Montar lista de writes: apenas linhas com resultado
# sheet row = index_in_data + 2 (1-based + header)
writes = []  # (sheet_row, cnpj, cpf)
for idx, aid in enumerate(account_ids):
    if aid in results:
        writes.append((idx + 2, results[aid]["cnpj"], results[aid]["cpf"]))

print(f"Linhas a escrever: {len(writes)}")

# 5. Escrever agrupando runs consecutivas (eficiente)
def flush(run):
    if not run:
        return
    start = run[0][0]
    end   = run[-1][0]
    values = [[r[1], r[2]] for r in run]
    google("sheets_write", spreadsheet_id=SPREADSHEET_ID,
           range_=f"{SHEET}!B{start}:C{end}", values=values)
    print(f"  Escrito B{start}:C{end} ({len(run)} linhas)")
    time.sleep(0.2)

run = []
for row_num, cnpj, cpf in writes:
    if run and (row_num != run[-1][0] + 1 or len(run) >= 1000):
        flush(run)
        run = []
    run.append((row_num, cnpj, cpf))
flush(run)

print(f"\nConcluído! {len(writes)} linhas preenchidas.")
