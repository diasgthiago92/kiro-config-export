import sys
import json
import psycopg2
import os
import warnings

warnings.filterwarnings("ignore")

# Função simples para carregar .env se existir
def load_env():
    env_path = os.path.expanduser('~/Documents/Main/Brain/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()

PROFILES = {
    'default': {
        'host': os.getenv('POSTGRES_HOST', 'vas-leads-db.olxbr.io'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'advertising_vas'),
        'user': os.getenv('POSTGRES_USER', 'consultas'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    },
    'vehicle_history': {
        'host': os.getenv('POSTGRES_HOST_VEHICLE', 'vas-autos-vehicle-history-db.olxbr.io'),
        'port': os.getenv('POSTGRES_PORT_VEHICLE', '5432'),
        'database': os.getenv('POSTGRES_DB_VEHICLE', 'vehicle_history_production'),
        'user': os.getenv('POSTGRES_USER_VEHICLE', 'consultas'),
        'password': os.getenv('POSTGRES_PASSWORD_VEHICLE', '')
    }
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
                                        "profile": {"type": "string", "enum": ["default", "vehicle_history"], "default": "default", "description": "Perfil de banco de dados a usar"}
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
                                        "profile": {"type": "string", "enum": ["default", "vehicle_history"], "default": "default", "description": "Perfil de banco de dados a usar"}
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
                
                if not conn_params['password'] or conn_params['password'] in ['SUA_SENHA_AQUI', 'NOVA_SENHA_AQUI', '']:
                    res_content = f"ERRO: Senha para o perfil '{profile}' não configurada no arquivo .env."
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
                            res_content = f"Banco: {conn_params['database']} - Comando executado com sucesso."
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
