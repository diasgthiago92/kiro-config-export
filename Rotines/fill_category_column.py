import json, subprocess, re

SHEET_ID = "1_Vf8dihfBruHrd7xhOREtstZr6RyD3HhPlMwf28G1x8"
ABA = "BASE_OMINI_202605 - BASE_OMNI_c"
BATCH_SIZE = 1000
TRINO_BRIDGE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
GOOGLE_BRIDGE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/google_bridge.py"

def google_call(tool, **args):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}})
    result = subprocess.run(["python3", GOOGLE_BRIDGE], input=payload, capture_output=True, text=True)
    out = json.loads(result.stdout)
    if "error" in out: raise Exception(out["error"])
    return json.loads(out["result"]["content"][0]["text"])

def trino_query(sql):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "query", "arguments": {"sql": sql, "schema": "ods"}}})
    result = subprocess.run(["python3", TRINO_BRIDGE], input=payload, capture_output=True, text=True)
    data = json.loads(result.stdout)
    if "error" in data: raise Exception(data["error"]["message"])
    return data["result"]["content"][0]["text"]

def parse_rows(raw):
    match = re.search(r"Dados: (\[.*\])", raw, re.DOTALL)
    if not match:
        return []
    s = match.group(1)
    s = re.sub(r"datetime\.\w+\([^)]+\)", '"dt"', s)
    s = s.replace("None", "null").replace("'", '"')
    try:
        return json.loads(s)
    except:
        return []

# Step 1: Read all list_ids (column N, index 13)
print("Lendo planilha...")
rows = google_call("sheets_read", spreadsheet_id=SHEET_ID, range_=f"'{ABA}'!N:N")
data_rows = rows[1:]  # skip header
list_ids = [r[0] for r in data_rows if r and r[0]]
print(f"Total list_ids: {len(list_ids)}")

# Step 2: Query Trino in batches — list_id_nk is bigint, category_id_fk per list_id
# Use MAX to get one value per list_id (should be unique)
category_map = {}
total_batches = (len(list_ids) + BATCH_SIZE - 1) // BATCH_SIZE

for i in range(0, len(list_ids), BATCH_SIZE):
    batch = list_ids[i:i + BATCH_SIZE]
    ids_str = ", ".join(batch)
    sql = f"""
SELECT list_id_nk, MAX(category_id_fk) AS category_id_fk
FROM hive.ods.ad
WHERE list_id_nk IN ({ids_str})
GROUP BY list_id_nk
"""
    batch_num = i // BATCH_SIZE + 1
    print(f"Batch {batch_num}/{total_batches}...", end=" ", flush=True)
    try:
        raw = trino_query(sql)
        result_rows = parse_rows(raw)
        for row in result_rows:
            if len(row) >= 2 and row[1] is not None:
                category_map[str(row[0])] = row[1]
        print(f"ok ({len(result_rows)} results)")
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\nCategories encontradas: {len(category_map)}")

# Step 3: Build column O values
o_values = [["category_id"]]
for row in data_rows:
    lid = str(row[0]) if row and row[0] else ""
    o_values.append([category_map.get(lid, "")])

# Step 4: Write in chunks of 5000
WRITE_BATCH = 5000
total_rows = len(o_values)
print(f"Escrevendo {total_rows} linhas na coluna O...")

for i in range(0, total_rows, WRITE_BATCH):
    chunk = o_values[i:i + WRITE_BATCH]
    start_row = i + 1
    end_row = i + len(chunk)
    google_call("sheets_write", spreadsheet_id=SHEET_ID, range_=f"'{ABA}'!O{start_row}:O{end_row}", values=chunk)
    print(f"  Escrito linhas {start_row}-{end_row}")

filled = sum(1 for v in o_values[1:] if v[0] != "")
empty = total_rows - 1 - filled
print(f"\nConcluído! {filled}/{total_rows-1} preenchidos, {empty} vazios.")
