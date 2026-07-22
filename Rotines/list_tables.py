import trino
import os
from trino.dbapi import connect
import warnings

warnings.filterwarnings("ignore")

TRINO_USER = os.environ.get('TRINO_USER', 'thiago.dias')
TRINO_PASSWORD = os.environ.get('TRINO_PASSWORD', '')

try:
    conn = connect(
        host='trino-gateway.dataeng.bigdata.olxbr.io',
        port=443,
        user=TRINO_USER,
        http_scheme='https',
        auth=trino.auth.BasicAuthentication(TRINO_USER, TRINO_PASSWORD),
        source='dataeng-trino-api'
    )
    cur = conn.cursor()
    cur.execute('SHOW TABLES FROM hive.ods')
    rows = cur.fetchall()
    print(f"Tabelas encontradas no schema 'ods':")
    for row in rows:
        print(f"- {row[0]}")
except Exception as e:
    print(f"Error: {e}")
