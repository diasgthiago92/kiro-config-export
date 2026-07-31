# Conexão PostgreSQL — Einstein

## Método obrigatório

Usar sempre o **MCP bridge**: `/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/postgres_bridge.py`  
Credenciais lidas automaticamente de `~/Documents/Brain/.env`.

## Perfis e tabelas

### `default` → `advertising_vas` ([INTERNAL_HOST_DEFAULT])
Schema: `public`
- safra_enabled_sellers
- audit_event_status_control
- santander_leads_last_four_days
- santander_leads_last_seven_days
- vas_events
- ad_tags
- audit_event / audit_event_type / audit_event_status_control
- financing_lead / financing_preference / financing_proposal / financing_simulation / financing_disclaimer_version
- knex_migrations / knex_migrations_lock / knex_migrations_vas_ad_enrich / knex_migrations_vas_ad_enrich_lock
- datalake_migration / lock_control_table

### `vehicle_history` → `vehicle_history_production` ([INTERNAL_HOST_VEHICLE])
Schema: `public`
- vehicle_histories
- vehicle_histories_provider_request
- vehicle_histories_admin_audit
- vehicle_histories_totals
- account_plate_reuse_allowlist
- unknown_restrictions
- goose_db_version
- temp_teste / temp_ad_events_rabbitmq

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
        ["python3", "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/postgres_bridge.py"],
        input=payload, capture_output=True, text=True
    )
    return json.loads(result.stdout)["result"]["content"][0]["text"]
```
