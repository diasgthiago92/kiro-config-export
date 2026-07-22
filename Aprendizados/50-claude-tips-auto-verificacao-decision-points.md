# 50 Claude Tips — Auto-verificação e Decision Points

**Data:** 20/07/2026  
**Fonte:** Infográfico "50 Claude Tips" (Mindstream) via LinkedIn

## Contexto

Infográfico com 50 dicas de uso avançado do Claude, cobrindo: seleção de modelo, prompts estruturados, Projects, Extended Thinking, MCP/Connectors, Cowork, Claude Code, memória entre sessões.

## Análise: o que já tínhamos vs. o que faltava

### Já coberto pelo nosso setup
- Model routing (Haiku/Sonnet/Opus) → implementado
- Role + goal + format + constraint → steerings
- "If unsure, say so" → comportamento nativo Kiro
- Projects com standing instructions → steerings + memoria-operacional
- MCP connectors → bridges
- Cowork (read/edit files) → Kiro CLI nativo
- /memory entre sessões → memoria-operacional.md + Aprendizados/

### O que faltava e foi implementado

#### 1. Auto-verificação antes de entregar (self-check)
- **Tip original:** "Before you finish, verify your work against these criteria"
- **Implementação:** Adicionado no steering do Jirinha — antes de retornar resultado, verifica: output responde o pedido? dados consistentes? formato segue padrões?
- **Arquivo:** `~/.kiro/steering/atlassian-agent.md`

#### 2. Decision points nomeados em análises
- **Tip original:** "Frame prompt as multi-step, name the decision points you want Claude to reason through"
- **Implementação:** Steering dedicado pro Einstein — toda análise deve ter perguntas específicas nomeadas, não prompts abertos. Inclui auto-verificação (todos os pontos respondidos? números batem? conclusão suportada por dados?).
- **Arquivo:** `~/Documents/Main/Brain/Steering/einstein-decision-points.md`

## Aprendizado-chave

A diferença entre output medíocre e output útil não é o modelo — é a **estrutura do prompt**. Decision points nomeados + auto-verificação contra critérios = agente que entrega com precisão na primeira tentativa em vez de precisar de 2-3 iterações de correção.
