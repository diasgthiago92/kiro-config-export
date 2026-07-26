# AI Agents Cheat Sheet — Análise e Melhorias

**Data:** 20/07/2026  
**Fonte:** Cheat sheet de Anastasiia Shapovalova (GenAI.Works) via LinkedIn

## Contexto

Mapa visual com taxonomia completa de AI Agents: Language Model, Tools (Extensions/Functions/Data Stores), Orchestration Layer (CoT, ToT, ReAct), Protocols (MCP, A2A) e categorias de agentes (One-Prompt, Workflow-Based, Coding Agents, Agentic Frameworks).

## Nosso posicionamento

Nosso setup se classifica como **Agentic Framework** — o nível mais avançado:
- Language Model: Claude (via Kiro CLI)
- Tools: Bridges MCP (postgres, trino, atlassian, google, slack)
- Orchestration: ReAct + Multi-agent com Manager pattern
- Protocols: MCP implementado, A2A parcial (sub-agents com depends_on)

---

## Melhorias identificadas

### 1. Routing de modelo por complexidade de tarefa (PRIORIDADE)

**Problema:** Usamos o mesmo modelo (Auto) para tudo — desde "mover issue no Jira" até "analisa inconsistências em 500 linhas de dados".

**O que o cheat sheet ensina:**
- LLMs (GPT-4o, Claude Sonnet) → tarefas médias a complexas
- SLMs (Gemma 3, Phi-4, Llama 3.x) → tarefas simples, on-device, budget limitado
- Reasoning Models (OpenAI o-series, Claude Opus, DeepSeek-R1) → lógica, step-by-step, deep analysis

**Melhoria proposta:** Quando o Kiro CLI suportar seleção de modelo por stage no subagent, rotear:
- Tasks simples (Jirinha: mover issue, criar task padronizada) → modelo leve/barato
- Análises complexas (Einstein: dados ambíguos, correlações) → reasoning model
- Tasks padrão (relatórios, buscas, listagens) → modelo default

**Status:** Aguardando suporte no Kiro CLI para `model` nos stages do subagent. Já existe o campo no schema — testar se funciona.

---

### 2. Data Stores como camada separada de Tools

**Problema:** Dados consultados com frequência (totais HV, safra ativa, métricas recorrentes) são buscados via query toda vez, consumindo tokens e tempo.

**Melhoria:** Cachear resultados de queries recorrentes como knowledge base, atualizadas pelas rotinas do LeoDias.

**Status:** Média prioridade. Implementar após validar o routing de modelo.

---

### 3. Decentralized vs Manager (confirmação)

Rotinas automatizadas (LeoDias) já operam em pattern decentralizado (crons independentes). Tasks sob demanda continuam no pattern Manager (eu → Kiro → sub-agent). Manter assim.

---

## Aprendizado-chave

O diferencial não é ter acesso ao modelo (commodity) nem ter tools conectadas. É a **qualidade da orquestração**: saber quando pensar mais (reasoning), quando agir rápido (SLM), e quando delegar (multi-agent). Nosso próximo salto é routing inteligente de modelo por complexidade.
