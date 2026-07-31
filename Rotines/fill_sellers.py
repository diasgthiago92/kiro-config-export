import json, subprocess, time

BRIDGE_TRINO = "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
BRIDGE_GOOGLE = "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/google_bridge.py"
SHEET_ID = "1J_JdlVt6zS8RAlV2fKgmy3bZUprlXYerRbvi4Q_gm6I"
TAB = "SELLERS"

def gcall(tool, **args):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}})
    r = subprocess.run(["python3", BRIDGE_GOOGLE], input=payload, capture_output=True, text=True)
    return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])

def trino(sql):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"query","arguments":{"sql":sql,"schema":"ods"}}})
    r = subprocess.run(["python3", BRIDGE_TRINO], input=payload, capture_output=True, text=True)
    data = json.loads(r.stdout)
    if "error" in data: raise Exception(data["error"])
    return data["result"]["content"][0]["text"]

def parse(text):
    result = {}
    for line in text.split('\n'):
        if line.startswith('Dados:'):
            for r in eval(line[6:].strip()):
                nk = str(r[0])
                cnpj, cpf = r[2] or '', r[1] or ''
                if nk not in result:
                    result[nk] = (cnpj, cpf)
                else:
                    old_cnpj, old_cpf = result[nk]
                    result[nk] = (cnpj or old_cnpj, cpf or old_cpf)
    return result

# Read A, B, C
rows = gcall("sheets_read", spreadsheet_id=SHEET_ID, range_=f"{TAB}!A1:C50000")
ids = [r[0] for r in rows[1:] if r]
existing_b = {i+2: (rows[i+1][1] if len(rows[i+1])>1 else '') for i in range(len(ids))}
existing_c = {i+2: (rows[i+1][2] if len(rows[i+1])>2 else '') for i in range(len(ids))}
print(f"Total: {len(ids)}")

# Find ids missing both B and C
missing_ids = list({ids[i] for i in range(len(ids)) if not existing_b[i+2] and not existing_c[i+2]})
print(f"IDs sem CPF/CNPJ: {len(missing_ids)}")

# Query Trino
mapping = {}
for i in range(0, len(missing_ids), 500):
    batch = missing_ids[i:i+500]
    sql = f"select account_id_nk, cpf, cnpj from hive.ods.account where account_id_nk in ({','.join(batch)})"
    print(f"Batch {i//500+1}/{(len(missing_ids)+499)//500}...", end=' ', flush=True)
    try:
        mapping.update(parse(trino(sql)))
        print("ok")
    except Exception as e:
        print(f"ERRO: {e}")
    time.sleep(0.2)

print(f"Encontrados: {len(mapping)}")

# Build update values only for rows missing data
b_vals = []
c_vals = []
for i, aid in enumerate(ids):
    row = i + 2
    cur_b = existing_b[row]
    cur_c = existing_c[row]
    if not cur_b and not cur_c and aid in mapping:
        cnpj, cpf = mapping[aid]
        b_vals.append((row, cnpj))
        c_vals.append((row, cpf))

print(f"Linhas a atualizar: {len(b_vals)}")

# Write individually only changed rows
for row, val in b_vals:
    gcall("sheets_write", spreadsheet_id=SHEET_ID, range_=f"{TAB}!B{row}", values=[[val]])
for i, (row, val) in enumerate(c_vals):
    gcall("sheets_write", spreadsheet_id=SHEET_ID, range_=f"{TAB}!C{row}", values=[[val]])
    if (i+1) % 500 == 0:
        print(f"  {i+1}/{len(c_vals)} escritos")

print("Concluído!")
