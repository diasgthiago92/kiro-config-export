# Conexão PostgreSQL — Einstein

## Método obrigatório

Usar sempre o **MCP bridge**: `~/Documents/Main/Brain/Bridges/postgres_bridge.py`  
Credenciais lidas automaticamente de `~/Documents/Brain/.env`.

## [CONFIGURAR] — Perfis e tabelas

### `default` → `[DB_NAME_DEFAULT]` ([HOST_DEFAULT])
Schema: `public`
- (listar tabelas do seu banco principal)

### `[PERFIL_2]` → `[DB_NAME_2]` ([HOST_2])
Schema: `public`
- (listar tabelas do segundo banco, se houver)

## Snippet Python

```python
import json, subprocess

def pg_query(sql, profile="default"):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "query", "arguments": {"sql": sql, "profile": profile}}
    })
    result = subprocess.run(
        ["python3", "~/Documents/Main/Brain/Bridges/postgres_bridge.py"],
        input=payload, capture_output=True, text=True
    )
    return json.loads(result.stdout)["result"]["content"][0]["text"]
```
