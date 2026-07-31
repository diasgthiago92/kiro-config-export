# Conexão Trino — Einstein

## Método obrigatório

O cliente `trino` CLI e a biblioteca Python `trino` com autenticação básica **não funcionam** diretamente contra o gateway (`[TRINO_GATEWAY_HOST]:443`). O método correto é via **MCP bridge**:

```python
import json, subprocess

def trino_query(query, schema="ods"):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "query", "arguments": {"sql": query, "schema": schema}}
    })
    result = subprocess.run(
        ["python3", "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"],
        input=payload, capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data["result"]["content"][0]["text"]

def trino_list_tables(schema="ods"):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "list_tables", "arguments": {"schema": schema}}
    })
    result = subprocess.run(
        ["python3", "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"],
        input=payload, capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data["result"]["content"][0]["text"]
```

## Config
- Bridge: `/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/trino_mcp_bridge.py`
- Catalog: `hive`, Schema padrão: `ods`
- Credenciais completas em `~/.kiro/einstein-config.json` (`trino.connection_method = "mcp_bridge"`)
