# Template — Criação de Tasks no Jira

## Quando usar
Quando o usuário pedir para "criar task(s) no Jira" usando o formato estruturado abaixo.

## Formato de entrada do usuário

```
Criar <N> tasks no Jira da seguinte forma:

Título: <título da task>
Plataforma: <Android / iOS / Android e iOS / Web / Backend>
Descrição: <descrição da task>
Critério de Aceite: <critério de aceite>
Quarter: <Q12026, Q22026, Q32026, Q42026>
Stack de Desenvolvimento: <ANDROID, IOS, BACKEND, FRONTEND>
Classificação da US: <Mapa Estratégico / BAU>
SPRINT: <nome da sprint>
```

## Comportamento esperado

1. Se `Plataforma` contiver mais de uma (ex: "Android / iOS"), criar **uma task separada por plataforma**, prefixando o título com `[Android]` ou `[iOS]`
2. Tipo de issue: `Task`
3. Incluir nos labels: quarter, stack de desenvolvimento, classificação da US
4. Mover a task para a sprint indicada (se possível)
5. Confirmar com o usuário antes de criar

## Exemplo

Entrada:
```
Criar 2 tasks no Jira da seguinte forma:

Título: Rollout - Hv One
Plataforma: Android / iOS
Descrição: Fazer rollout do teste Hv One para 100%
Critério de Aceite: Fazer rollout do teste Hv One para 100%
Quarter: Q32026
Stack de Desenvolvimento: ANDROID, IOS
Classificação da US: Mapa Estratégico
SPRINT: Sprint 24 - Hexa babou
```

Resultado: criar 2 tasks:
- `[Android] Rollout - Hv One`
- `[iOS] Rollout - Hv One`

Cada uma com:
- Tipo: Task
- Descrição: "Fazer rollout do teste Hv One para 100%"
- Labels: `Q32026`, `Mapa_Estratégico`, stack correspondente (`ANDROID` ou `IOS`)
- Sprint: Sprint 24 - Hexa babou
