# Kiro CLI — Pacote de Configuração para PMs

## O que é isso
Este pacote contém todos os steerings (arquivos de instrução) que configuram o comportamento do Kiro CLI para um Product Manager do time VAS/APRI.

## Como instalar

1. Copie a pasta `steering/` para `~/.kiro/steering/`
2. Copie a pasta `brain/` para `~/Documents/Main/Brain/`
3. Edite os arquivos marcados com `[CONFIGURAR]` substituindo os placeholders pelos seus dados reais
4. Configure o arquivo `~/Documents/Brain/.env` com suas credenciais

## Estrutura

```
kiro-config-export/
├── README.md                          ← Este arquivo
├── steering/                          ← Copiar para ~/.kiro/steering/
│   ├── 00-vpn-autoconnect.md          ← VPN check automático
│   ├── atlassian-agent.md             ← Jirinha (Jira + Confluence)
│   ├── jira-task-template.md          ← Template de criação de tasks
│   ├── einstein-postgres-connection.md ← Conexão PostgreSQL
│   ├── einstein-trino-connection.md   ← Conexão Trino/Hive
│   ├── einstein-decision-points.md    ← Decision points em análises
│   ├── model-routing.md              ← Routing de modelo por complexidade
│   ├── memoria-operacional.md        ← Erros conhecidos (memória entre sessões)
│   ├── googlinho.md                  ← Google Drive/Sheets/Slides/Gmail
│   ├── leodias-rotinas.md            ← Rotinas automatizadas
│   ├── vangogh-designer.md           ← Agente de design
│   ├── rtk-performance.md           ← RTK token optimizer
│   └── contatos.md                   ← Atalhos de contato
└── env.example                        ← Template de variáveis de ambiente
```

## Placeholders para substituir

Busque por `[CONFIGURAR]` nos arquivos e substitua:
- `[SEU_EMAIL]` → seu email @olxbr.com
- `[SEU_USUARIO]` → seu username no sistema
- `[PROJETO_JIRA]` → key do seu projeto no Jira
- `[BOARD_ID]` → ID do board Scrum no Jira
- `[ESPACO_CONFLUENCE]` → key do espaço Confluence
- `[PASTA_SPRINTS_ID]` → ID da pasta de sprints no Confluence
- `[SLACK_CHANNEL_ID]` → ID do canal Slack para notificações

## Pré-requisitos

- Kiro CLI instalado
- Python 3.x
- Bridges MCP instalados (postgres_bridge.py, trino_mcp_bridge.py, atlassian_bridge.py, google_bridge.py, slack_bridge.py)
- RTK (Rust Token Killer) instalado via `cargo install rtk`
- Acesso VPN configurado (FortiClient)
- Credenciais no .env (ver env.example)
