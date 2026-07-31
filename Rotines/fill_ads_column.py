import json, subprocess, re
from collections import defaultdict

SHEET_ID = "1J_JdlVt6zS8RAlV2fKgmy3bZUprlXYerRbvi4Q_gm6I"
SHEET_NAME = "SELLERS"
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

# Step 1: Read all rows (A and D columns)
print("Lendo planilha...")
rows = google_call("sheets_read", spreadsheet_id=SHEET_ID, range_=f"{SHEET_NAME}!A:D")
data_rows = rows[1:]
print(f"Total linhas de dados: {len(data_rows)}")

# Group by periodo
by_period = defaultdict(list)
for idx, row in enumerate(data_rows):
    aid = row[0] if len(row) > 0 and row[0] else None
    periodo = row[3] if len(row) > 3 and row[3] else None
    if aid and periodo and len(str(periodo)) == 6:
        by_period[str(periodo)].append((idx, str(aid)))

# ads_map: (account_id_nk, periodo) -> count
ads_map = {}

for periodo, items in sorted(by_period.items()):
    year = int(periodo[:4])
    month = int(periodo[4:6])
    account_ids = list({aid for _, aid in items})
    total_batches = (len(account_ids) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nPeriodo {periodo} ({len(account_ids)} accounts, {total_batches} batches)...")

    for i in range(0, len(account_ids), BATCH_SIZE):
        batch = account_ids[i:i + BATCH_SIZE]
        ids_str = ", ".join(batch)
        # Join ods.ad com ods.account via account_id_pk = account_id_fk
        sql = f"""
SELECT ac.account_id_nk, COUNT(DISTINCT ad.list_id_nk) AS cnt
FROM hive.ods.ad ad
JOIN hive.ods.account ac ON ac.account_id_pk = ad.account_id_fk
WHERE ac.account_id_nk IN ({ids_str})
  AND ad.year = {year}
  AND ad.month = {month}
GROUP BY ac.account_id_nk
"""
        batch_num = i // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches}...", end=" ", flush=True)
        try:
            raw = trino_query(sql)
            result_rows = parse_rows(raw)
            for row in result_rows:
                if len(row) >= 2:
                    ads_map[(str(row[0]), periodo)] = row[1]
            print(f"ok ({len(result_rows)} results)")
        except Exception as e:
            print(f"ERROR: {e}")

print(f"\nTotal entradas no ads_map: {len(ads_map)}")

# Step 2: Build column L values
l_values = [["Ads"]]
for row in data_rows:
    aid = row[0] if len(row) > 0 and row[0] else None
    periodo = row[3] if len(row) > 3 and row[3] else None
    val = ads_map.get((str(aid), str(periodo)), "") if aid and periodo else ""
    l_values.append([val])

# Step 3: Write in chunks of 5000
WRITE_BATCH = 5000
total_rows = len(l_values)
print(f"Escrevendo {total_rows} linhas na coluna L...")

for i in range(0, total_rows, WRITE_BATCH):
    chunk = l_values[i:i + WRITE_BATCH]
    start_row = i + 1
    end_row = i + len(chunk)
    google_call("sheets_write", spreadsheet_id=SHEET_ID, range_=f"{SHEET_NAME}!L{start_row}:L{end_row}", values=chunk)
    print(f"  Escrito linhas {start_row}-{end_row}")

filled = sum(1 for v in l_values[1:] if v[0] != "")
print(f"\nConcluído! {filled}/{total_rows-1} linhas preenchidas com contagem de ads.")
