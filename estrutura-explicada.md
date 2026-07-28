# Kiro CLI — Estrutura Simplificada + Explicação

## Versão Visual (Simplificada)

```
┌─────────────────────┐
│      KIRO CLI        │
│   (Default Agent)    │
└──────────┬──────────┘
           │
    ┌──────┼──────┬──────────────┐
    │      │      │              │
    ▼      ▼      ▼              ▼
STEERING  SKILLS  COMMANDS  KNOWLEDGE BASES
```

**STEERING** — Regras sempre ativas (vpn-autoconnect, model-routing, rtk-performance, etc.)
**SKILLS** — Playbooks passo-a-passo (data-analysis, experiment-design, sprint-report, etc.)
**COMMANDS** — Atalhos executáveis por categoria (rotina, sprint, dados, comunicação, pesquisa)
**KNOWLEDGE BASES** — Documentos indexados com busca semântica (B3 Financiamentos, VAS)

```
    │
    ▼
┌──────────────────────────────────┐
│           AGENTES (6)            │
│                                  │
│  Einstein · Jirinha · Googlinho  │
│  LeoDias · Van Gogh · GitHub     │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│        BRIDGES MCP (7)           │
│     (JSON-RPC via Python)        │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│      SERVIÇOS EXTERNOS           │
│  (PostgreSQL, Trino, Jira,       │
│   Google, Slack, GitHub, Figma)  │
└──────────────────────────────────┘
```

**Infra:** Model Routing (Sonnet/Auto/Haiku) · RTK (compressor) · FortiClient VPN · Credenciais (.env)

---

## Versão Explicada — O que é cada item

### 🧠 KIRO CLI (Default Agent)
O cérebro central. É o agente principal que recebe seus pedidos, decide qual ferramenta ou sub-agente usar, e orquestra tudo. Roda no terminal via `kiro-cli chat`.

---

### 📐 STEERING (Regras Persistentes)
Arquivos `.md` em `~/.kiro/steering/` que definem **comportamento permanente** — carregados em toda sessão sem precisar repetir instruções. São as "leis" que o Kiro sempre obedece.

| Steering | O que faz |
|----------|-----------|
| `vpn-autoconnect` | Verifica VPN antes de qualquer ação; abre FortiClient se desconectada |
| `model-routing` | Escolhe modelo certo por complexidade (Sonnet para análise, Haiku para tasks mecânicas) |
| `rtk-performance` | Comprime output de comandos shell para economizar tokens |
| `memoria-operacional` | Registro de erros conhecidos para não repetir (tipo um "lessons learned") |
| `atlassian-agent` | Config do Jirinha: projeto APRI, board, emails do time, tools disponíveis |
| `einstein-pg` | Config de conexão PostgreSQL (bancos, perfis, tabelas) |
| `einstein-trino` | Config de conexão Trino/Hive (data lake) |
| `googlinho` | Config do Google Workspace (Drive, Sheets, Slides, Gmail) |
| `vangogh-designer` | Config do agente de design (revisão de layouts, specs) |
| `slack-listas` | Listas de membros + Slack IDs para envio em massa |
| `contatos` | Atalhos de envio (ex: "envia pro Ton" → DM no Slack) |
| `cowork-modes` | Modos de interação: Brainstorm, Estratégia, Reviewer, Professor, Planejador, Debate |
| `debate-analises` | Pattern Analyst vs Challenger para análises de dados com contra-argumentos |
| `aidlc-vas` | Processo de delivery de produto em 3 steps (Discovery → Design → Tech) |
| `humboldt-research` | Pesquisa profunda autônoma com wiki + backlinks |

---

### 📚 SKILLS (Playbooks)
Workflows estruturados passo-a-passo em `~/.kiro/skills/`. Diferentes de steerings porque têm **etapas sequenciais** com inputs e outputs definidos.

| Skill | O que faz |
|-------|-----------|
| `data-analysis` | Analisa dados com decision points obrigatórios (não aceita "analise tudo") |
| `experiment-design` | Desenha testes A/B com hipótese, sample size, critérios de sucesso |
| `hypothesis` | Formaliza hipóteses de produto testáveis |
| `jira-task-creation` | Cria tasks no Jira com template padronizado do time |
| `launch-checklist` | Checklist de rollout (nada esquecido antes de ir pra produção) |
| `meeting-recap` | Transforma reunião em decisões + action items |
| `sprint-report` | Gera e publica sprint report no Confluence |
| `weekly-report` | Executa rotinas de relatórios automáticos |
| `handoff` | Gera documento para continuar sessão em outro LLM/sessão |
| `content-pipeline` | Fluxo de criação de conteúdo (ideia → pesquisa → rascunho → revisão) |
| `create-skill` | Wizard para criar novos skills |
| `market-intelligence` | Intel de mercado (financiamento de veículos, B3, competidores) |
| `stakeholder-update` | Updates estruturados para liderança/time |

---

### ⚡ COMMANDS (Atalhos Executáveis)
Comandos em `~/.kiro/commands/` que executam ações diretas com um trigger. Organizados por categoria:

**Rotina (dia-a-dia):**
| Comando | O que faz |
|---------|-----------|
| `morning-brief` | Resumo matinal: sprint, issues, emails, calendário |
| `end-of-day` | Fechamento do dia: o que foi feito, pendências |
| `check-mail` | Lista emails não lidos (Gmail) |
| `check-calendar` | Próximos eventos do calendário |

**Sprint/Jira:**
| Comando | O que faz |
|---------|-----------|
| `sprint-health` | Saúde da sprint: burndown, blockers, velocity |
| `weekly-status` | Status semanal do time |
| `my-issues` | Minhas issues abertas |
| `blocked` | Issues bloqueadas no board |

**Dados:**
| Comando | O que faz |
|---------|-----------|
| `leads-hoje` | Leads de financiamento gerados hoje |
| `financ-pulse` | Pulso diário do produto de financiamento |
| `hv-status` | Status do produto Histórico Veicular |
| `market-intel` | Intelligence de mercado (B3 + fontes) |

**Comunicação:**
| Comando | O que faz |
|---------|-----------|
| `send-update` | Envia update formatado via Slack |
| `recap` | Gera recap de reunião/conversa |

**Produtividade:**
| Comando | O que faz |
|---------|-----------|
| `deploy` / `deploy-vercel` / `deploy-github` | Deploy de projetos |
| `make-video` | Cria roteiro/storyboard para vídeo |
| `make-deck` | Cria apresentação (Google Slides) |

**Sistema:**
| Comando | O que faz |
|---------|-----------|
| `vpn-check` | Testa se a VPN está conectada |
| `rtk-stats` | Mostra economia de tokens do RTK |

**Pesquisa (Humboldt):**
| Comando | O que faz |
|---------|-----------|
| `autodeepsearch` | Pesquisa profunda autônoma em múltiplos ciclos |
| `drill` | Aprofunda um ponto específico |
| `synthesize` | Re-sintetiza wiki após novos drills |
| `archive` / `clean` / `zip` | Gerenciamento de pesquisas anteriores |

---

### 📖 KNOWLEDGE BASES
Documentos indexados com busca semântica. O Kiro consulta quando precisa de contexto específico sem ocupar a context window.

| KB | Conteúdo |
|----|----------|
| B3 — Financ. de Veículos (24–26) | Dados públicos da B3 sobre mercado de financiamento veicular |
| VAS Financ. OLX | Documentação interna do produto de financiamento da OLX |

---

### 🤖 AGENTES (6 sub-agentes especializados)
Cada agente tem um domínio e é chamado pelo Default Agent quando necessário:

| Agente | Especialidade |
|--------|---------------|
| **Einstein** | Executa queries SQL (PostgreSQL + Trino), analisa dados, cria gráficos |
| **Jirinha** | Gerencia Jira (criar/mover issues, sprints) e Confluence (páginas, sprint reports) |
| **Googlinho** | Opera Drive, Sheets, Slides e Gmail |
| **LeoDias** | Roda rotinas automáticas (relatórios agendados) e envia notificações Slack |
| **Van Gogh** | Revisa layouts Figma, documenta processos, cria specs de design |
| **GitHub** | PRs, issues, branches, code review |

---

### 🔌 BRIDGES MCP (Camada de Comunicação)
Scripts Python que implementam o protocolo JSON-RPC (MCP — Model Context Protocol) para comunicar com serviços externos. São a "cola" entre os agentes e os serviços reais.

| Bridge | Conecta com |
|--------|-------------|
| `postgres_bridge.py` | Bancos PostgreSQL internos (leads, vehicle history) |
| `trino_mcp_bridge.py` | Data lake Trino/Hive (tabelas ODS) |
| `atlassian_bridge.py` | Jira + Confluence (olxbr.atlassian.net) |
| `google_bridge.py` | Google APIs (Drive, Sheets, Slides, Gmail) |
| `slack_bridge.py` | Slack API para envio de mensagens |
| `Figma MCP` | Figma API (design tokens) |
| `gh CLI` | GitHub via CLI nativa |

---

### 🌐 SERVIÇOS EXTERNOS
Os sistemas reais que os bridges acessam. Maioria requer VPN corporativa (FortiClient).

| Serviço | Endpoint |
|---------|----------|
| PostgreSQL | vas-leads-db.olxbr.io / vas-autos-vehicle-history-db.olxbr.io |
| Trino/Hive | trino-gateway.dataeng.bigdata.olxbr.io:443 |
| Atlassian | olxbr.atlassian.net (Jira + Confluence) |
| Google | googleapis.com (Drive/Sheets/Slides/Gmail) |
| Slack | slack.com/api |
| GitHub | github.com |
| Figma | api.figma.com |

---

### ⚙️ INFRA (Rodapé)

| Item | O que é |
|------|---------|
| **Model Routing** | 3 tiers: Sonnet (análise pesada), Auto (default), Haiku (tasks mecânicas) — otimiza custo/qualidade |
| **Credenciais** | `.env` com tokens, Service Account do Google, config do Einstein |
| **RTK** | Compressor de output — reduz tokens gastos em comandos shell (git, grep, etc.) |
| **FortiClient VPN** | Obrigatória para acessar bancos e serviços internos |
| **Hooks** | Automações que disparam em eventos (ex: pré-commit) |
| **Extensions** | Plugins adicionais (como Humboldt para pesquisa profunda) |
