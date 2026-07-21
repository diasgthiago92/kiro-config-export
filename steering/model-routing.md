# Model Routing — Regras de seleção de modelo por complexidade

## Princípio
Usar o modelo certo para a complexidade certa. Modelo pesado para análise profunda, modelo leve para execução mecânica.

## Modelos disponíveis

| Tier | Modelo | Usar para |
|------|--------|-----------|
| **Reasoning** | `claude-sonnet-4-20250514` | Análises complexas, correlações de dados, decisões com múltiplas variáveis, debugging |
| **Default** | *(Auto — não especificar)* | Tasks padrão, relatórios, buscas, conversação |
| **Light** | `claude-haiku-3-20250310` | Tasks mecânicas: mover issue, criar task padronizada, formatar dados, listar itens |

## Quando aplicar

### Usar Reasoning (especificar model no stage)
- Agente de dados analisando dados ambíguos ou cruzando múltiplas tabelas
- Debugging de queries que retornam resultados inesperados
- Decisões de arquitetura ou planejamento
- Análise de texto longo (Confluence, documentos)

### Usar Default (não especificar model)
- Relatórios estruturados
- Buscas no Jira/Confluence
- Criação de conteúdo
- Maioria das tarefas do dia-a-dia

### Usar Light (especificar model haiku)
- Mover issues no Jira (transições simples)
- Criar tasks com template já definido
- Formatar/transformar dados já estruturados
- Listagens simples (páginas, sprints, arquivos)

## Como usar no subagent

```python
# Task complexa → reasoning
{"model": "claude-sonnet-4-20250514", "name": "analise", "role": "einstein", ...}

# Task padrão → default (não especificar model)
{"name": "relatorio", "role": "leodias", ...}

# Task mecânica → light
{"model": "claude-haiku-3-20250310", "name": "mover_issues", "role": "jirinha", ...}
```

## Regra de decisão rápida

> Se a task tem resposta óbvia e formato fixo → Light  
> Se a task precisa de julgamento mas é rotineira → Default  
> Se a task pode ter múltiplas respostas corretas e precisa de raciocínio → Reasoning
