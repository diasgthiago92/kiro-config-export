# Estrutura — Mapa Visual do Kiro CLI

## Quando usar
Quando o usuário pedir "estrutura", "mostra a estrutura", "mapa do kiro", ou "como tá configurado" — exibir EXATAMENTE o bloco abaixo, sem alterações:

## Output

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                              KIRO CLI — ARQUITETURA                                        ║
║                         Time VAS (APRI/APS1) · ~/.kiro/                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝


                                ┌─────────────────────┐
                                │      KIRO CLI        │
                                │   (Default Agent)    │
                                └──────────┬──────────┘
                                           │
         ┌───────────────┼───────────────┼───────────────┐
         │               │               │               │
         ▼               ▼               ▼               ▼
┌──────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│    STEERING       │ │     SKILLS       │ │    COMMANDS      │ │  KNOWLEDGE BASES (10)    │
│ (regras persist.) │ │ (playbooks)      │ │ (~/.kiro/commands) │ │                         │
│                   │ │                  │ │                  │ │ Financiamento & Crédito: │
│ • vpn-autoconnect │ │ • data-analysis  │ │ Rotina:          │ │ • B3/SNG — Financiam.   │
│ • rtk-performance │ │ • experiment-    │ │ • morning-brief  │ │   de Veículos (20–26)   │
│ • memoria-oper.   │ │   design         │ │ • end-of-day     │ │ • Banco Central — SCR   │
│ • atlassian-agent │ │ • hypothesis     │ │ • check-mail     │ │   + SGS (crédito veic.) │
│ • einstein-pg     │ │ • jira-task-     │ │ • check-calendar │ │                         │
│ • einstein-trino  │ │   creation       │ │                  │ │ Vendas & Produção:      │
│ • googlinho       │ │ • launch-        │ │ Sprint/Jira:     │ │ • Fenabrave — Emplac.   │
│ • vangogh-design. │ │   checklist      │ │ • sprint-health  │ │   de Veículos Novos     │
│ • slack-listas    │ │ • meeting-recap  │ │ • weekly-status  │ │ • Fenauto — Vendas de   │
│ • contatos        │ │ • sprint-report  │ │ • my-issues      │ │   Veículos Usados       │
│ • cowork-modes    │ │ • weekly-report  │ │ • blocked        │ │ • ANFAVEA — Produção    │
│ • debate-kiro-gem.│ │ • handoff        │ │                  │ │   e Licenciamentos      │
│ • aidlc-vas       │ │ • create-skill   │ │ Dados:           │ │                         │
│ • humboldt-res.   │ │ • market-intel   │ │ • leads-hoje     │ │ Frota & Preços:         │
│ • model-routing   │ │ • stakeholder-   │ │ • financ.-pulse  │ │ • SENATRAN/RENAVAM —    │
│ • debate-analises │ │   update         │ │ • hv-status      │ │   Frota Nacional        │
│                   │ │ • content-       │ │ • market-intel   │ │ • FIPE — Tabela de      │
│                   │ │   pipeline       │ │                  │ │   Preços de Veículos    │
│                   │ │                  │ │ Comunicação:     │ │                         │
│                   │ │                  │ │ • send-update    │ │ Seguros & Contexto:     │
│                   │ │                  │ │ • recap          │ │ • SUSEP — Seguros       │
│                   │ │                  │ │                  │ │   Automotivos           │
│                   │ │                  │ │ Produtividade:   │ │ • IBGE — PNAD + IPCA    │
│                   │ │                  │ │ • deploy         │ │   Veículos              │
│                   │ │                  │ │ • deploy-vercel  │ │                         │
│                   │ │                  │ │ • deploy-github  │ │ Mercado:                │
│                   │ │                  │ │ • make-video     │ │ • Classificados — OLX   │
│                   │ │                  │ │ • make-deck      │ │   / Webmotors           │
│                   │ │                  │ │                  │ │                         │
│                   │ │                  │ │ Sistema:         │ └─────────────────────────┘
│                   │ │                  │ │ • vpn-check      │
│                   │ │                  │ │ • rtk-stats      │
│                   │ │                  │ │                  │
│                   │ │                  │ │ Pesquisa:        │
│                   │ │                  │ │ • autodeepsearch │
│                   │ │                  │ │ • drill          │
│                   │ │                  │ │ • synthesize     │
│                   │ │                  │ │ • archive        │
│                   │ │                  │ │ • clean          │
│                   │ │                  │ │ • zip            │
│                   │ │                  │ │                  │
└──────────────────┘ └─────────────────┘ └─────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                     AGENTES (5)                                          │
│                                                                                          │
│   • Einstein ───── Analista de Dados (PostgreSQL + Trino/Hive)                           │
│   • Jirinha ────── Jira + Confluence (projeto APRI, board 1358)                          │
│   • Googlinho ──── Google Workspace (Drive, Sheets, Slides, Gmail)                       │
│   • LeoDias ────── Rotinas automáticas + notificações Slack                              │
│   • Van Gogh ───── Designer (revisão layouts, specs, documentação)                       │
│                                                                                          │
└──────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              BRIDGES MCP (JSON-RPC)                                       │
│                                                                                          │
│   • postgres_bridge.py ──── PostgreSQL (advertising_vas, vehicle_history)                 │
│   • trino_mcp_bridge.py ── Trino/Hive (hive.ods.*)                                      │
│   • atlassian_bridge.py ── Jira + Confluence (olxbr.atlassian.net)                       │
│   • google_bridge.py ───── Drive, Sheets, Slides, Gmail                                  │
│   • gemini_bridge.py ───── Gemini (Antigravity CLI, debate entre LLMs)                   │
│   • slack_bridge.py ────── Slack API (bot token)                                         │
│   • Figma MCP ─────────── Design tokens, styles                                         │
│   • gh CLI ─────────────── GitHub (via MCP)                                              │
│   • Appium MCP ─────────── Automação mobile (Android emulator + iOS simulator)           │
│                                                                                          │
└──────────────────────────────────────────┬───────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         SERVIÇOS EXTERNOS (VPN obrigatória)                               │
│                                                                                          │
│   PostgreSQL ─── vas-leads-db.olxbr.io / vas-autos-vehicle-history-db.olxbr.io           │
│   Trino/Hive ── trino-gateway.dataeng.bigdata.olxbr.io:443                              │
│   Atlassian ─── olxbr.atlassian.net (Jira + Confluence)                                  │
│   Google ────── googleapis.com (Drive/Sheets/Slides/Gmail)                               │
│   Slack ─────── slack.com/api                                                            │
│   GitHub ────── github.com                                                               │
│   Figma ─────── api.figma.com                                                           │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  CREDENCIAIS:    .env (tokens) │ google_service_account │ einstein-config.json            │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  INFRA:          RTK (compress output) │ FortiClient VPN │ Android Emulator │ Hooks │ Ext.│
└──────────────────────────────────────────────────────────────────────────────────────────┘
```
