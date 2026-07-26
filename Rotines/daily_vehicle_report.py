import os
import psycopg2
import pandas as pd
import logging
import json
import subprocess
from datetime import datetime

log_file = "/Users/thiago.dias/daily_vehicle_report.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def load_env():
    env_path = os.path.expanduser('~/Documents/Main/Brain/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key.strip()] = value.strip()

def check_connectivity(host):
    import socket
    try:
        socket.getaddrinfo(host, 5432)
        return True
    except socket.gaierror:
        return False

def send_slack_message(message, recipients):
    for channel in recipients:
        payload = json.dumps({
            "jsonrpc": "2.0", "id": 1,
            "method": "tools/call",
            "params": {"name": "send_message", "arguments": {"channel": channel, "text": message}}
        })
        result = subprocess.run(
            ["python3", "/Users/thiago.dias/Documents/Main/Brain/Bridges/slack_bridge.py"],
            input=payload, capture_output=True, text=True
        )
        resp = json.loads(result.stdout)
        logging.info(resp["result"]["content"][0]["text"])

def run_report():
    load_env()

    host = os.getenv("POSTGRES_HOST_VEHICLE")
    database = os.getenv("POSTGRES_DB_VEHICLE")
    user = os.getenv("POSTGRES_USER_VEHICLE")
    password = os.getenv("POSTGRES_PASSWORD_VEHICLE")
    port = os.getenv("POSTGRES_PORT_VEHICLE", "5432")

    if not check_connectivity(host or 'vas-autos-vehicle-history-db.olxbr.io'):
        msg = f"⚠️ *daily_vehicle_report* não executou: sem acesso a `{host}`. Verifique a VPN."
        send_slack_message(msg, ["C0B2X8FQ81M"])
        logging.error(f"Sem conectividade com {host}. VPN ativa?")
        return

    query = """
    SELECT
        CURRENT_DATE AS data_referencia,
        COUNT(*) AS total_registros
    FROM vehicle_histories_provider_request vhpr
    JOIN vehicle_histories AS vh ON vh.vh_id = vhpr.vh_id
    WHERE provider_endpoint = 'webhook'
      AND provider_response_code = 'SUCCESS'
      AND requested_at >= date_trunc('month', CURRENT_DATE)
      AND requested_at <= CURRENT_TIMESTAMP;
    """

    conn = None
    try:
        logging.info("Iniciando consulta no banco vehicle_history_production...")

        if not password or password == 'NOVA_SENHA_AQUI':
            logging.error("ERRO: Senha não configurada no .env (POSTGRES_PASSWORD_VEHICLE).")
            return

        conn = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        df = pd.read_sql_query(query, conn)
        total = df['total_registros'].iloc[0]
        logging.info(f"Relatório gerado com sucesso. Total: {total}")

        export_dir = "/Users/thiago.dias/Documents/Vehicle Reports"
        os.makedirs(export_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        file_path = os.path.join(export_dir, f"daily_vehicle_count_{timestamp}.csv")
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        logging.info(f"Arquivo exportado para: {file_path}")

        percentage = (total / 50000) * 100
        remaining = 50000 - total

        recipients = ["C0B2X8FQ81M", "U08DUDN607Q"]

        if total >= 50000:
            msg = (
                f"Seu consumo mensal de Histórico Veicular é de {total}, isso corresponde a {percentage:.2f}% do total. "
                f"Nosso custo já caiu para R$ 1,10."
            )
        else:
            msg = (
                f"Seu consumo mensal de Histórico Veicular é de {total}, isso corresponde a {percentage:.2f}% do total. "
                f"Lembre-se que ainda faltam {remaining} para nosso valor unitário ir de 1,87 para 1,10."
            )
        send_slack_message(msg, recipients)

    except Exception as e:
        logging.error(f"Erro ao executar o relatório: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("Conexão encerrada.")

if __name__ == "__main__":
    run_report()
