import json, subprocess, re

SHEET_ID = "16XqoHP5spKHvE7HmeRPqNYm4YiZXL6IANxNku08u6gU"
SHEET_NAME = "Página1"
BATCH_SIZE = 1000
TRINO_BRIDGE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
GOOGLE_BRIDGE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/google_bridge.py"

def google_call(tool, **args):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}})
    result = subprocess.run(["python3", GOOGLE_BRIDGE], input=payload, capture_output=True, text=True)
    return json.loads(json.loads(result.stdout)["result"]["content"][0]["text"])

def trino_query(sql):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "query", "arguments": {"sql": sql, "schema": "ods"}}})
    result = subprocess.run(["python3", TRINO_BRIDGE], input=payload, capture_output=True, text=True)
    data = json.loads(result.stdout)
    if "error" in data:
        raise Exception(data["error"]["message"])
    return data["result"]["content"][0]["text"]

def parse_trino_result(raw):
    """Parse 'Colunas: [...]\nDados: [...]' format"""
    match = re.search(r"Dados: (\[.*\])", raw, re.DOTALL)
    if not match:
        return []
    # Safe eval-like parse using json after cleaning datetime objects
    dados_str = match.group(1)
    # Replace datetime objects with string representation
    dados_str = re.sub(r"datetime\.datetime\([^)]+\)", '"datetime"', dados_str)
    dados_str = re.sub(r"datetime\.date\([^)]+\)", '"date"', dados_str)
    dados_str = dados_str.replace("None", "null").replace("'", '"')
    try:
        return json.loads(dados_str)
    except:
        return []

# Step 1: Read ALL account_ids from column A (skip header)
print("Lendo planilha...")
rows = google_call("sheets_read", spreadsheet_id=SHEET_ID, range_=f"{SHEET_NAME}!A:A")
account_ids = [r[0] for r in rows[1:] if r and r[0]]  # skip header, skip empty
print(f"Total account_ids: {len(account_ids)}")

# Step 2: Query Trino in batches of 1000 — get active profile (most recent) per account
profile_map = {}
total_batches = (len(account_ids) + BATCH_SIZE - 1) // BATCH_SIZE

for i in range(0, len(account_ids), BATCH_SIZE):
    batch = account_ids[i:i + BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    ids_str = ", ".join(batch)  # bigint, no quotes

    # Get active profile with latest last_status_update per account_id
    sql = f"""
SELECT account_id, profile
FROM (
    SELECT account_id, profile,
           ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY last_status_update DESC) AS rn
    FROM hive.ods.profile
    WHERE account_id IN ({ids_str})
      AND status = 'active'
) t
WHERE rn = 1
"""
    print(f"Batch {batch_num}/{total_batches} ({len(batch)} ids)...", end=" ", flush=True)
    
    try:
        raw = trino_query(sql)
        rows_data = parse_trino_result(raw)
        for row in rows_data:
            if len(row) >= 2 and row[1]:
                profile_map[str(row[0])] = row[1]
        print(f"ok ({len(rows_data)} results)")
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\nProfiles encontrados: {len(profile_map)}")

# Step 3: Build column B values and write back
all_rows = google_call("sheets_read", spreadsheet_id=SHEET_ID, range_=f"{SHEET_NAME}!A:A")
b_values = [["profile"]]  # header
for row in all_rows[1:]:
    aid = str(row[0]) if row and row[0] else ""
    b_values.append([profile_map.get(aid, "")])

# Write in chunks of 5000 rows
WRITE_BATCH = 5000
total_rows = len(b_values)
print(f"Escrevendo {total_rows} linhas na coluna B...")

for i in range(0, total_rows, WRITE_BATCH):
    chunk = b_values[i:i + WRITE_BATCH]
    start_row = i + 1
    end_row = i + len(chunk)
    google_call("sheets_write", spreadsheet_id=SHEET_ID, range_=f"{SHEET_NAME}!B{start_row}:B{end_row}", values=chunk)
    print(f"  Escrito linhas {start_row}-{end_row}")

filled = sum(1 for v in b_values[1:] if v[0] != "")
print(f"\nConcluído! {filled}/{total_rows-1} linhas preenchidas com profile.")
