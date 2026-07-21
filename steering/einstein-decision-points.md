# Einstein — Decision Points em Análises

## Regra
Quando o Einstein receber uma tarefa analítica (não mecânica), o prompt deve incluir **decision points nomeados** — perguntas específicas que o agente deve responder, em vez de deixar aberto "analise isso".

## Por que
Sem decision points, o agente decide sozinho o que é relevante. Resultado: análises genéricas, foco errado, ou informação importante ignorada.

## Como aplicar

### ❌ Prompt aberto (evitar)
```
Analise a tabela vehicle_histories e me diga o que está acontecendo.
```

### ✅ Prompt com decision points (usar)
```
Analise a tabela vehicle_histories respondendo:
1. Volume diário mudou vs semana passada? (>10% = significativo)
2. Há concentração em algum provider específico?
3. Taxa de erro está dentro do esperado (<5%)?
4. Algum padrão anômalo nos últimos 3 dias?
```

## Quando aplicar
- Análises exploratórias de dados
- Comparações entre períodos
- Diagnóstico de problemas
- Qualquer pedido que comece com "analise", "investigue", "verifique"

## Quando NÃO aplicar
- Queries diretas com resposta objetiva ("quantos registros tem?")
- Listagens simples
- Extração de dados com formato já definido

## Auto-verificação do Einstein
Antes de entregar análise, verificar:
1. Todos os decision points foram respondidos?
2. Os números batem com a query executada?
3. Se há conclusão, ela é suportada pelos dados — ou é suposição?

Se for suposição, declarar explicitamente: "Suposição: [X]. Precisaria de [Y] para confirmar."
