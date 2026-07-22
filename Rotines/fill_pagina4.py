import json, subprocess, time

BRIDGE_TRINO = "/Users/thiago.dias/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
BRIDGE_GOOGLE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/google_bridge.py"
SHEET_ID = "1J_JdlVt6zS8RAlV2fKgmy3bZUprlXYerRbvi4Q_gm6I"
TAB = "Página4"

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
                    # keep non-empty values
                    old_cnpj, old_cpf = result[nk]
                    result[nk] = (cnpj or old_cnpj, cpf or old_cpf)
    return result

# Read all account_ids
rows = gcall("sheets_read", spreadsheet_id=SHEET_ID, range_=f"{TAB}!A1:A50000")
ids = [r[0] for r in rows[1:] if r]
print(f"Total: {len(ids)}")

# Query in batches of 500
mapping = {}
for i in range(0, len(ids), 500):
    batch = ids[i:i+500]
    sql = f"select account_id_nk, cpf, cnpj from hive.ods.account where account_id_nk in ({','.join(batch)})"
    print(f"Batch {i//500+1}/{(len(ids)+499)//500}...", end=' ', flush=True)
    try:
        mapping.update(parse(trino(sql)))
        print("ok")
    except Exception as e:
        print(f"ERRO: {e}")
    time.sleep(0.2)

print(f"Encontrados: {len(mapping)}")

# Build B (CNPJ) and C (CPF) columns
b_vals = [[mapping.get(aid, ('',''))[0]] for aid in ids]
c_vals = [[mapping.get(aid, ('',''))[1]] for aid in ids]

# Write in chunks of 1000
for i in range(0, len(ids), 1000):
    s, e = i+2, i+2+len(b_vals[i:i+1000])-1
    gcall("sheets_write", spreadsheet_id=SHEET_ID, range_=f"{TAB}!B{s}:B{e}", values=b_vals[i:i+1000])
    gcall("sheets_write", spreadsheet_id=SHEET_ID, range_=f"{TAB}!C{s}:C{e}", values=c_vals[i:i+1000])
    print(f"Escrito linhas {s}-{e}")

print("Concluído!")
