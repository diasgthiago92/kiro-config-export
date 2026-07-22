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
    return data["result"]["content"][0]["text"]

def parse_trino(text):
    result = {}
    for line in text.strip().split('\n'):
        if line.startswith('Dados:'):
            rows = eval(line[len('Dados:'):].strip())
            for row in rows:
                nk, cpf, cnpj = str(row[0]), row[1] or '', row[2] or ''
                result[nk] = (cnpj, cpf)
    return result

# Step 1: Read A, B, C
print("Lendo planilha...")
rows = google_call("sheets_read", spreadsheet_id=SHEET_ID, range_="SELLERS!A1:C47000")
print(f"Total linhas: {len(rows)-1}")

# Step 2: Find rows missing both B and C
missing_rows = []  # (row_index_1based, account_id)
for i, row in enumerate(rows[1:], start=2):
    aid = row[0] if row else ''
    cnpj = row[1] if len(row) > 1 else ''
    cpf  = row[2] if len(row) > 2 else ''
    if aid and not cnpj and not cpf:
        missing_rows.append((i, aid))

print(f"Linhas sem CPF e sem CNPJ: {len(missing_rows)}")

# Step 3: Query Trino for missing ids
missing_ids = list({aid for _, aid in missing_rows})
print(f"IDs únicos a buscar: {len(missing_ids)}")

mapping = {}
BATCH = 500
total = (len(missing_ids) + BATCH - 1) // BATCH
for i in range(0, len(missing_ids), BATCH):
    batch = missing_ids[i:i+BATCH]
    ids_str = ','.join(batch)
    sql = f"select account_id_nk, cpf, cnpj from hive.ods.account where account_id_nk in ({ids_str})"
    bn = i//BATCH+1
    print(f"Batch {bn}/{total}...", end=' ', flush=True)
    try:
        text = trino_query(sql)
        m = parse_trino(text)
        mapping.update(m)
        print(f"ok ({len(m)} encontrados)")
    except Exception as e:
        print(f"ERRO: {e}")
    time.sleep(0.2)

print(f"\nTotal mapeados: {len(mapping)}")

# Step 4: Write only rows that were missing and now have data
# Group consecutive rows for batch writes
updates_b = {}  # row -> cnpj
updates_c = {}  # row -> cpf

for row_idx, aid in missing_rows:
    if aid in mapping:
        cnpj, cpf = mapping[aid]
        if cnpj:
            updates_b[row_idx] = cnpj
        if cpf:
            updates_c[row_idx] = cpf

print(f"Linhas com CNPJ para preencher: {len(updates_b)}")
print(f"Linhas com CPF para preencher: {len(updates_c)}")

# Write individually (or in small batches by range)
# Write B column updates
written = 0
for row_idx, val in updates_b.items():
    google_call("sheets_write", spreadsheet_id=SHEET_ID,
                range_=f"SELLERS!B{row_idx}", values=[[val]])
    written += 1
    if written % 100 == 0:
        print(f"  B: {written}/{len(updates_b)} escritos")

print(f"  B: {written} total escritos")

written = 0
for row_idx, val in updates_c.items():
    google_call("sheets_write", spreadsheet_id=SHEET_ID,
                range_=f"SELLERS!C{row_idx}", values=[[val]])
    written += 1
    if written % 100 == 0:
        print(f"  C: {written}/{len(updates_c)} escritos")

print(f"  C: {written} total escritos")
print("Concluído!")
