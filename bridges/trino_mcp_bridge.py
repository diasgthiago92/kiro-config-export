"""
Trino/Hive MCP Bridge
Protocolo: JSON-RPC 2.0 via stdin/stdout
Tools: query, list_tables
Dependência: pip install trino

[CONFIGURAR] Edite CONN_PARAMS com seu host, user e credenciais.
"""
import sys
import json
import os
import trino
from trino.dbapi import connect
import warnings

warnings.filterwarnings("ignore")

# [CONFIGURAR] Substitua com suas credenciais Trino
TRINO_USER = os.environ.get('TRINO_USER', 'seu.usuario')
TRINO_PASSWORD = os.environ.get('TRINO_PASSWORD', '')

# [CONFIGURAR] Substitua com seu host Trino
CONN_PARAMS = {
    'host': os.environ.get('TRINO_HOST', 'trino-gateway.seu-dominio.io'),
    'port': 443,
    'user': TRINO_USER,
    'http_scheme': 'https',
    'auth': trino.auth.BasicAuthentication(TRINO_USER, TRINO_PASSWORD),
    'source': 'mcp-bridge'
}

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            request = json.loads(line)
            id = request.get("id")
            method = request.get("method")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {"name": "trino-bridge", "version": "1.0.0"}
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "tools": [
                            {
                                "name": "query",
                                "description": "Executa uma query SQL no Trino",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "sql": {"type": "string"},
                                        "schema": {"type": "string", "default": "ods"}
                                    },
                                    "required": ["sql"]
                                }
                            },
                            {
                                "name": "list_tables",
                                "description": "Lista tabelas de um schema no Hive",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "schema": {"type": "string"}
                                    },
                                    "required": ["schema"]
                                }
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                tool_name = request["params"]["name"]
                args = request["params"].get("arguments", {})
                
                conn = connect(**CONN_PARAMS)
                cur = conn.cursor()
                
                if tool_name == "query":
                    cur.execute(args["sql"])
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    max_rows = int(args.get("max_rows", 10000))
                    res_content = f"Colunas: {cols}\nDados: {rows[:max_rows]}"
                elif tool_name == "list_tables":
                    cur.execute(f"SHOW TABLES FROM hive.{args['schema']}")
                    rows = cur.fetchall()
                    res_content = "\n".join([r[0] for r in rows])
                
                response = {
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "content": [{"type": "text", "text": res_content}]
                    }
                }
            else:
                response = {"jsonrpc": "2.0", "id": id, "error": {"code": -32601, "message": "Method not found"}}
            
            print(json.dumps(response), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": id, "error": {"message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()
