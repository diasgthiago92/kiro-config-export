# Stack de Economia de Tokens — Arquitetura Consolidada

**Data:** 20/07/2026

## Visão geral

Estrutura em camadas para otimizar consumo de tokens no setup Kiro CLI + sub-agents + bridges MCP.

## Camadas ativas

### 1. Camada de Entrada — RTK (Rust Token Killer)
- Comprime outputs de terminal antes de entrar no contexto (git, npm, builds, logs, Docker)
- Local: `/opt/homebrew/bin/rtk`
- Status: ✅ Ativo

### 2. Camada de Orquestração — Model Routing
- Light (Haiku) → tasks mecânicas (~10x mais barato)
- Default (Auto) → tasks rotineiras
- Reasoning (Sonnet) → análises complexas
- Config: `~/Documents/Main/Brain/Steering/model-routing.md`
- Status: ✅ Ativo e testado

### 3. Camada de Controle — Escopo Fechado
- Agente só faz o que foi pedido
- Fora de escopo explícito corta ações extras
- Preview antes de batch (>3 itens)
- Premissas assumidas declaradas no output
- Config: steering do Jirinha
- Status: ✅ Ativo

### 4. Camada de Saída — System Prompt Conciso
- Nativo do Kiro CLI ("Be concise and direct", "Skip filler")
- Não precisa de ferramenta externa (Caveman redundante)
- Status: ✅ Nativo

## Camadas futuras (a investigar)

### 5. Context Mode (MCP layer)
- Filtraria outputs volumosos dos bridges (queries SQL, listagens Confluence/Drive)
- Status: 🔍 Pendente avaliação de compatibilidade

### 6. Data Stores (Knowledge Base cache)
- Cachear queries recorrentes como KB em vez de rodar query toda vez
- Status: 🔍 Média prioridade

## Economia estimada

| Camada | O que economiza | Impacto |
|--------|----------------|---------|
| RTK | Tokens de input (outputs de terminal) | Alto |
| Model Routing | Custo por token (modelo certo pra task) | Alto |
| Escopo fechado | Tokens de output (corta ações extras) | Médio |
| System prompt conciso | Tokens de output (sem filler) | Já nativo |
| Context Mode (futuro) | Tokens de input (dados volumosos) | Potencialmente alto |
| Data Stores cache (futuro) | Tokens de input + latência | Médio |

## Teste realizado

Model Routing com Haiku listou sprint inteira (17 issues) com sucesso — mesma qualidade que Sonnet pra task mecânica, fração do custo.
