# Memória Operacional — Erros conhecidos e lições aprendidas

## Propósito
Este arquivo registra erros que já aconteceram durante execução dos agentes. Antes de executar uma tarefa, consultar se há lição relevante aqui para não repetir o mesmo erro.

## Regra
Quando um erro novo acontecer E for resolvido, adicionar uma entrada aqui com:
- **Contexto:** o que estava sendo feito
- **Erro:** o que deu errado
- **Causa:** por que aconteceu
- **Solução:** como resolver / evitar

---

## Jira

### Transições de status têm ordem obrigatória
- **Contexto:** Mover issue de Backlog direto pra Code Review
- **Erro:** Transição rejeitada pela API
- **Causa:** O workflow do Jira exige passar por estados intermediários
- **Solução:** Sempre verificar status atual antes de transicionar. Sequência válida: Backlog → Priorizado para Desenvolvimento → Em andamento → Code Review

### Labels usam underscore, não espaço
- **Contexto:** Criar issue com label "Mapa Estratégico"
- **Erro:** Label criado com espaço, ficou inconsistente com os existentes
- **Causa:** Jira aceita espaço mas o padrão do time usa underscore
- **Solução:** Sempre usar `Mapa_Estratégico`, `Tech_Value`, etc.

---

## Trino/Hive

### Queries grandes precisam de LIMIT
- **Contexto:** SELECT * em tabela do ODS sem LIMIT
- **Erro:** Timeout ou retorno de dados gigante que estoura contexto
- **Causa:** Tabelas ODS têm milhões de linhas
- **Solução:** Sempre usar LIMIT (padrão: 100) em queries exploratórias. Só remover quando o usuário pedir explicitamente.

---

## PostgreSQL

*(adicionar conforme erros acontecerem)*

---

## Google/Drive

*(adicionar conforme erros acontecerem)*

---

## Rotinas (LeoDias)

*(adicionar conforme erros acontecerem)*
