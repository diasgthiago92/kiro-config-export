import json, subprocess, time

BRIDGE_TRINO = "/Users/thiago.dias/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
BRIDGE_GOOGLE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/google_bridge.py"
SHEET_ID = "1J_JdlVt6zS8RAlV2fKgmy3bZUprlXYerRbvi4Q_gm6I"

def google_call(tool, **args):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}})
    r = subprocess.run(["python3", BRIDGE_GOOGLE], input=payload, capture_output=True, text=True)
    return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])

def trino_query(sql):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"query","arguments":{"sql":sql,"schema":"ods"}}})
    r = subprocess.run(["python3", BRIDGE_TRINO], input=payload, capture_output=True, text=True)
    data = json.loads(r.stdout)
    if "error" in data:
        raise Exception(data["error"])
    return json.loads(r.stdout)["result"]["content"][0]["text"]

def parse_trino_result(text):
    # Returns dict: account_id_nk -> (cnpj, cpf)
    result = {}
    lines = text.strip().split('\n')
    for line in lines:
        if line.startswith('Dados:'):
            rows_str = line[len('Dados:'):].strip()
            rows = eval(rows_str)
            for row in rows:
                nk, cpf, cnpj = row[0], row[1], row[2]
                result[str(nk)] = (cnpj or '', cpf or '')
    return result

# Step 1: Read all rows from sheet
print("Lendo planilha...")
raw = google_call("sheets_read", spreadsheet_id=SHEET_ID, range_="SELLERS!A1:A47000")
rows = raw  # list of lists
account_ids = [r[0] for r in rows[1:] if r]  # skip header
print(f"Total account_ids: {len(account_ids)}")

# Step 2: Query Trino in batches of 500
BATCH = 500
mapping = {}
total_batches = (len(account_ids) + BATCH - 1) // BATCH

for i in range(0, len(account_ids), BATCH):
    batch = account_ids[i:i+BATCH]
    batch_num = i // BATCH + 1
    ids_str = ','.join(batch)
    sql = f"select account_id_nk, cpf, cnpj from hive.ods.account where account_id_nk in ({ids_str})"
    print(f"Batch {batch_num}/{total_batches}...", end=' ', flush=True)
    try:
        text = trino_query(sql)
        batch_map = parse_trino_result(text)
        mapping.update(batch_map)
        print(f"ok ({len(batch_map)} encontrados)")
    except Exception as e:
        print(f"ERRO: {e}")
    time.sleep(0.3)

print(f"\nTotal mapeados: {len(mapping)}")

# Step 3: Build M and N columns (CNPJ=M, CPF=N), starting row 2
print("Preparando dados para escrita...")
m_values = []
n_values = []
for aid in account_ids:
    cnpj, cpf = mapping.get(str(aid), ('', ''))
    m_values.append([cnpj])
    n_values.append([cpf])

# Step 4: Write to sheet in chunks
WRITE_CHUNK = 1000
total_rows = len(m_values)
print(f"Escrevendo {total_rows} linhas nas colunas M e N...")

for i in range(0, total_rows, WRITE_CHUNK):
    chunk_m = m_values[i:i+WRITE_CHUNK]
    chunk_n = n_values[i:i+WRITE_CHUNK]
    start_row = i + 2  # row 1 is header
    end_row = start_row + len(chunk_m) - 1
    
    google_call("sheets_write", spreadsheet_id=SHEET_ID,
                range_=f"SELLERS!M{start_row}:M{end_row}", values=chunk_m)
    google_call("sheets_write", spreadsheet_id=SHEET_ID,
                range_=f"SELLERS!N{start_row}:N{end_row}", values=chunk_n)
    print(f"  Linhas {start_row}-{end_row} escritas")

print("Concluído!")
