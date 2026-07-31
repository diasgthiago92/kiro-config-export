# Googlinho — Google Drive, Sheets, Slides e Gmail

## Identidade
Agente responsável pelo acesso ao Google Workspace: Drive, Sheets, Slides e Gmail.

## Arquivos
- Bridge MCP: `/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/google_bridge.py`
- Agente CLI: `/Users/[YOUR_USER]/Documents/Main/Brain/Agents/google_agent.py`
- Service Account (Drive/Sheets/Slides): `~/.kiro/google_service_account.json`
- OAuth2 credentials (Gmail): `~/.kiro/google_credentials.json` *(necessário apenas para Gmail)*
- Token OAuth2 salvo: `~/.kiro/google_token.json`

## Autenticação
- **Drive, Sheets, Slides**: Service Account `[SERVICE_ACCOUNT_EMAIL]` — sem setup adicional
- **Gmail**: OAuth2 — requer `~/.kiro/google_credentials.json` (baixar do GCP Console) na primeira execução
- **Importante**: Para acessar arquivos do Drive pessoal, compartilhe-os com `[SERVICE_ACCOUNT_EMAIL]`

## Como chamar o bridge

```python
import json, subprocess

def google_call(tool, **args):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    })
    result = subprocess.run(
        ["python3", "/Users/[YOUR_USER]/Documents/Main/Brain/Bridges/google_bridge.py"],
        input=payload, capture_output=True, text=True
    )
    return json.loads(json.loads(result.stdout)["result"]["content"][0]["text"])
```

## Tools disponíveis

### Drive
| Tool | Parâmetros |
|------|-----------|
| `drive_list` | `query` (opcional), `max_results` |
| `drive_search` | `name`, `max_results` |
| `drive_get_file` | `file_id` |
| `drive_create_folder` | `name`, `parent_id` (opcional) |

### Sheets
| Tool | Parâmetros |
|------|-----------|
| `sheets_read` | `spreadsheet_id`, `range_` (ex: `Sheet1!A1:D10`) |
| `sheets_write` | `spreadsheet_id`, `range_`, `values` (lista de listas) |
| `sheets_append` | `spreadsheet_id`, `range_`, `values` |
| `sheets_create` | `title` |
| `sheets_get_info` | `spreadsheet_id` |

### Slides
| Tool | Parâmetros |
|------|-----------|
| `slides_get` | `presentation_id` |
| `slides_create` | `title` |
| `slides_add_text_slide` | `presentation_id`, `title_text`, `body_text` |

### Gmail
| Tool | Parâmetros |
|------|-----------|
| `gmail_list` | `max_results`, `query` |
| `gmail_read` | `message_id` |
| `gmail_send` | `to`, `subject`, `body`, `reply_to_id` (opcional) |
| `gmail_search` | `query`, `max_results` |
| `gmail_mark_read` | `message_id` |

## Comandos CLI

```bash
# Drive
python3 google_agent.py drive-list
python3 google_agent.py drive-search "relatório"
python3 google_agent.py drive-list "mimeType='application/vnd.google-apps.spreadsheet'"

# Sheets
python3 google_agent.py sheets-info <spreadsheet_id>
python3 google_agent.py sheets-read <spreadsheet_id> "Sheet1!A1:E10"
python3 google_agent.py sheets-append <spreadsheet_id> "Sheet1!A:A" '[["valor1","valor2"]]'

# Slides
python3 google_agent.py slides-get <presentation_id>

# Gmail
python3 google_agent.py gmail-list
python3 google_agent.py gmail-list "from:alguem@gmail.com"
python3 google_agent.py gmail-read <message_id>
python3 google_agent.py gmail-search "subject:reunião"
python3 google_agent.py gmail-send "dest@email.com" "Assunto" "Corpo do e-mail"
```

## Setup inicial (OAuth2)

1. Acesse https://console.cloud.google.com/
2. Crie um projeto (ou use um existente)
3. Ative as APIs: Drive API, Sheets API, Slides API, Gmail API
4. Em "Credenciais" → "Criar credenciais" → "ID do cliente OAuth 2.0"
5. Tipo: **Aplicativo para computador**
6. Baixe o JSON e salve em `~/.kiro/google_credentials.json`
7. Execute qualquer comando — o browser abrirá para autorização
8. O token será salvo automaticamente em `~/.kiro/google_token.json`

## Dependências Python

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```
