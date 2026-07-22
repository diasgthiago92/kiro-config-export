import os
import pandas as pd
import psycopg2
import json
import subprocess
from datetime import datetime

def load_env():
    env_path = os.path.expanduser('~/Documents/Main/Brain/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

def check_connectivity(host):
    import socket
    try:
        socket.getaddrinfo(host, 5432)
        return True
    except socket.gaierror:
        return False

def send_slack_message(message):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "send_message", "arguments": {"channel": "C0B2X8FQ81M", "text": message}}
    })
    result = subprocess.run(
        ["python3", "/Users/thiago.dias/Documents/Main/Brain/Bridges/slack_bridge.py"],
        input=payload, capture_output=True, text=True
    )
    resp = json.loads(result.stdout)
    print(resp["result"]["content"][0]["text"])

CONN_PARAMS = {
    'host': os.getenv('POSTGRES_HOST', 'vas-leads-db.olxbr.io'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'advertising_vas'),
    'user': os.getenv('POSTGRES_USER', 'consultas'),
    'password': os.getenv('POSTGRES_PASSWORD', '')
}

QUERY = """
SELECT DISTINCT ON (fs.transaction_id)
    fs.transaction_id, fs.status, fs.creation_date, fs.cet,
    fs.proposal_id, fs.transaction_type, fl.buyer_document
FROM financing_simulation fs
INNER JOIN financing_lead fl ON fs.transaction_id = fl.transaction_id
WHERE fs.creation_date >= date_trunc('week', current_date - interval '1 week')
  AND fs.creation_date < date_trunc('week', current_date)
  AND fs.status = 'NEEDS_PROPOSAL_DATA'
  AND fs.bank = 'safra'
ORDER BY fs.transaction_id, fs.creation_date DESC;
"""

def main():
    try:
        host = os.getenv('POSTGRES_HOST', 'vas-leads-db.olxbr.io')
        if not check_connectivity(host):
            send_slack_message(f"⚠️ *weekly_vas_report* não executou: sem acesso a `{host}`. Verifique a VPN.")
            return

        print(f"[{datetime.now()}] Iniciando extração semanal...")
        conn = psycopg2.connect(**CONN_PARAMS)
        df = pd.read_sql_query(QUERY, conn)

        timestamp = datetime.now().strftime("%Y%m%d")
        output_dir = "/Users/thiago.dias/Documents/Safra Report Semanal"
        os.makedirs(output_dir, exist_ok=True)

        base_filename = f"safra_report_aprovados_{timestamp}"
        temp_path = os.path.join(output_dir, f"{base_filename}_full.csv")
        df.to_csv(temp_path, index=False, encoding='utf-8-sig')
        file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)

        if file_size_mb > 50:
            num_parts = int(-(file_size_mb // -24.9))
            rows_per_part = len(df) // num_parts + 1
            for i in range(num_parts):
                part_name = f"{base_filename}_part{i+1}.csv"
                part_path = os.path.join(output_dir, part_name)
                df.iloc[i*rows_per_part:(i+1)*rows_per_part].to_csv(part_path, index=False, encoding='utf-8-sig')
                send_slack_message(f"weekly_vas_report.py foi executada com sucesso e o arquivo {part_name} foi gerado.")
            os.remove(temp_path)
        else:
            final_name = f"{base_filename}.csv"
            final_path = os.path.join(output_dir, final_name)
            os.rename(temp_path, final_path)
            send_slack_message(f"weekly_vas_report.py foi executada com sucesso e o arquivo {final_name} foi gerado.")

        print(f"Linhas totais extraídas: {len(df)}")
        conn.close()

    except Exception as e:
        send_slack_message(f"❌ *ERRO no Relatório Safra Aprovados!*\n- Erro: {str(e)}")
        print(f"[{datetime.now()}] ERRO: {str(e)}")

if __name__ == "__main__":
    main()
