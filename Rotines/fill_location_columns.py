import json, subprocess, re

SHEET_ID = "1_Vf8dihfBruHrd7xhOREtstZr6RyD3HhPlMwf28G1x8"
ABA = "BASE_OMINI_202605 - BASE_OMNI_c"
BATCH_SIZE = 1000
TRINO_BRIDGE = "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
GOOGLE_BRIDGE = "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/google_bridge.py"

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

# Step 1: Read all list_ids (column N)
print("Lendo planilha...")
rows = google_call("sheets_read", spreadsheet_id=SHEET_ID, range_=f"'{ABA}'!N:N")
data_rows = rows[1:]
list_ids = [r[0] for r in data_rows if r and r[0]]
print(f"Total list_ids: {len(list_ids)}")

# Step 2: Query Trino in batches
location_map = {}  # list_id -> (municipality_name, state_code)
total_batches = (len(list_ids) + BATCH_SIZE - 1) // BATCH_SIZE

for i in range(0, len(list_ids), BATCH_SIZE):
    batch = list_ids[i:i + BATCH_SIZE]
    ids_str = ", ".join(batch)
    sql = f"""
SELECT ad.list_id_nk, MAX(loc.municipality_name) AS municipality_name, MAX(are.state_code) AS state_code
FROM hive.ods.ad ad
LEFT JOIN hive.ods.dm_location loc ON ad.location_id_fk = loc.location_id_pk
LEFT JOIN hive.ods.dm_area are ON ad.area_id_fk = are.area_id_nk
WHERE ad.list_id_nk IN ({ids_str})
GROUP BY ad.list_id_nk
"""
    batch_num = i // BATCH_SIZE + 1
    print(f"Batch {batch_num}/{total_batches}...", end=" ", flush=True)
    try:
        raw = trino_query(sql)
        result_rows = parse_rows(raw)
        for row in result_rows:
            if len(row) >= 3:
                location_map[str(row[0])] = (row[1] or "", row[2] or "")
        print(f"ok ({len(result_rows)} results)")
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\nLocalizações encontradas: {len(location_map)}")

# Step 3: Build columns P and Q
pq_values = [["municipality_name", "state_code"]]
for row in data_rows:
    lid = str(row[0]) if row and row[0] else ""
    mun, state = location_map.get(lid, ("", ""))
    pq_values.append([mun, state])

# Step 4: Write in chunks of 5000
WRITE_BATCH = 5000
total_rows = len(pq_values)
print(f"Escrevendo {total_rows} linhas nas colunas P e Q...")

for i in range(0, total_rows, WRITE_BATCH):
    chunk = pq_values[i:i + WRITE_BATCH]
    start_row = i + 1
    end_row = i + len(chunk)
    google_call("sheets_write", spreadsheet_id=SHEET_ID, range_=f"'{ABA}'!P{start_row}:Q{end_row}", values=chunk)
    print(f"  Escrito linhas {start_row}-{end_row}")

filled = sum(1 for v in pq_values[1:] if v[0] != "" or v[1] != "")
print(f"\nConcluído! {filled}/{total_rows-1} linhas preenchidas.")
