"""
PostgreSQL MCP Bridge
Protocolo: JSON-RPC 2.0 via stdin/stdout
Tools: query, list_tables
Dependência: pip install psycopg2-binary

[CONFIGURAR] Edite os PROFILES com seus hosts, bancos e credenciais.
Credenciais vêm do arquivo .env (ver env.example na raiz do repo).
"""
import sys
import json
import psycopg2
import os
import warnings

warnings.filterwarnings("ignore")

def load_env():
    env_path = os.path.expanduser('~/Documents/Main/Brain/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()

# [CONFIGURAR] Adicione/modifique perfis conforme seus bancos
PROFILES = {
    'default': {
        'host': os.getenv('POSTGRES_HOST', 'seu-host-db.exemplo.io'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'seu_banco'),
        'user': os.getenv('POSTGRES_USER', 'seu_usuario'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    },
    # Adicione mais perfis conforme necessário:
    # 'outro_banco': {
    #     'host': os.getenv('POSTGRES_HOST_OUTRO', 'outro-host.exemplo.io'),
    #     'port': '5432',
    #     'database': os.getenv('POSTGRES_DB_OUTRO', 'outro_banco'),
    #     'user': os.getenv('POSTGRES_USER_OUTRO', 'usuario'),
    #     'password': os.getenv('POSTGRES_PASSWORD_OUTRO', '')
    # }
}

def get_conn_params(profile_name):
    return PROFILES.get(profile_name, PROFILES['default'])

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
                        "serverInfo": {"name": "postgres-bridge", "version": "1.1.0"}
                    }
                }
            elif method == "tools/list":
                profile_names = list(PROFILES.keys())
                response = {
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "tools": [
                            {
                                "name": "query",
                                "description": "Executa uma query SQL no PostgreSQL",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "sql": {"type": "string"},
                                        "profile": {"type": "string", "enum": profile_names, "default": "default"}
                                    },
                                    "required": ["sql"]
                                }
                            },
                            {
                                "name": "list_tables",
                                "description": "Lista tabelas do schema public ou especificado",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "schema": {"type": "string", "default": "public"},
                                        "profile": {"type": "string", "enum": profile_names, "default": "default"}
                                    },
                                    "required": []
                                }
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                tool_name = request["params"]["name"]
                args = request["params"].get("arguments", {})
                profile = args.get("profile", "default")
                conn_params = get_conn_params(profile)
                
                if not conn_params['password'] or conn_params['password'] == '':
                    res_content = f"ERRO: Senha para o perfil '{profile}' não configurada no .env"
                else:
                    conn = psycopg2.connect(**conn_params)
                    cur = conn.cursor()
                    
                    if tool_name == "query":
                        cur.execute(args["sql"])
                        if cur.description:
                            rows = cur.fetchall()
                            cols = [d[0] for d in cur.description]
                            res_content = f"Banco: {conn_params['database']}\nColunas: {cols}\nDados: {rows[:100]}"
                        else:
                            conn.commit()
                            res_content = f"Banco: {conn_params['database']} - Comando executado."
                    elif tool_name == "list_tables":
                        schema = args.get("schema", "public")
                        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (schema,))
                        rows = cur.fetchall()
                        res_content = f"Tabelas em {conn_params['database']} ({schema}):\n" + "\n".join([r[0] for r in rows])
                    
                    cur.close()
                    conn.close()
                
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
