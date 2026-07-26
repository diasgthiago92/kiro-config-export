# Awesome LLM Apps — Patterns e Gaps identificados

**Data:** 20/07/2026  
**Fonte:** Repositório Awesome LLM Apps (100+ aplicações com LLMs) via LinkedIn

## Contexto

Repositório open source (Apache 2.0) com implementações prontas de RAG, multiagente, MCP, memória persistente, fine-tuning, busca híbrida e mais. Analisado contra nosso stack pra identificar o que já temos e o que está faltando.

## O que já temos coberto

| Pattern | Nosso equivalente |
|---|---|
| RAG | Knowledge base B3 (semantic search) |
| Multiagente com orquestração | Sub-agents com depends_on + model routing |
| MCP integrations | Bridges (postgres, trino, atlassian, google, slack) |
| Memória persistente | Knowledge bases + steerings + pasta Aprendizados |
| Roteamento entre modelos | Model routing (Haiku/Auto/Sonnet) |

## Gaps a investigar

### 1. Corrective RAG
- **O que é:** Agente avalia se o resultado da KB é relevante antes de usar. Se não for, reformula a query ou busca em outra fonte.
- **Onde aplica pra nós:** Einstein buscando na KB da B3 — hoje usa resultado tangencial sem questionar.
- **Impacto:** Médio. Melhora qualidade de análises baseadas em knowledge base.
- **Quando:** Quando a KB crescer mais e falsos positivos aumentarem.

### 2. Busca híbrida (semantic + keyword/BM25)
- **O que é:** Combina semantic search com keyword matching. Semantic pega contexto, keyword pega termos exatos.
- **Onde aplica pra nós:** Buscas na KB da B3 com termos técnicos específicos (nomes de instituições, códigos) que semantic search não resolve bem.
- **Impacto:** Médio.
- **Quando:** Se KB da B3 apresentar falsos positivos frequentes.

### 3. Memória episódica entre sessões
- **O que é:** Agente lembra de decisões e erros de sessões passadas sem KB explícita.
- **Onde aplica pra nós:** LeoDias detectar padrões de falha recorrente e mudar estratégia automaticamente.
- **Impacto:** Baixo agora.
- **Quando:** Futuro, se volume de rotinas crescer.

## O que NÃO vale implementar

| Pattern | Motivo |
|---------|--------|
| Fine-tuning (Gemma 3, Llama 3.2) | Usamos API, custo de manter modelo próprio não compensa |
| Saídas estruturadas (Pydantic) | Bridges já retornam JSON estruturado |
| Agentes de voz | Não temos caso de uso |

## Aprendizado-chave

Nosso stack está arquiteturalmente maduro comparado ao catálogo. Os gaps são de **refinamento** (corrective RAG, busca híbrida), não de fundação. O repositório serve como referência pra consultar quando precisar implementar um pattern específico.
