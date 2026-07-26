# Spec-Driven Development — Melhorias aplicáveis à nossa stack

**Data:** 20/07/2026  
**Fonte:** Post LinkedIn sobre template SDD (Spec-Driven Development)

## Contexto

Template de desenvolvimento orientado a spec com lifecycle de aprovação humana, exploração de código real antes da escrita, escopo fechado e evidência obrigatória para conclusão. Analisei o que desse fluxo pode melhorar nosso setup Kiro CLI + sub-agents + bridges.

---

## Melhorias concretas para nossa stack

### 1. Escopo negativo nos prompts de sub-agents

**Problema hoje:** Quando delego para Einstein, Jirinha ou LeoDias, o prompt diz o que fazer mas não diz o que NÃO fazer. Resultado: agente às vezes "melhora" algo adjacente, gerando ruído ou mudança não solicitada.

**Melhoria:** Incluir nos prompts dos sub-agents uma linha de restrição:
```
Escopo: [tarefa específica]
Fora de escopo: [o que não tocar, não alterar, não sugerir]
```

**Onde aplicar:** `prompt_template` dos stages no `subagent()`.

---

### 2. Premissas declaradas no output dos sub-agents

**Problema hoje:** Sub-agents tomam decisões (qual coluna filtrar, qual formato usar, qual sprint considerar) e entregam o resultado sem declarar o que assumiram. Se a premissa estiver errada, só descubro no resultado final.

**Melhoria:** Pedir nos prompts que o agente declare:
```
## Premissas assumidas
- [decisão que tomei sem perguntar + justificativa]
```

**Onde aplicar:** Prompts do Einstein (queries), Jirinha (criação de issues), LeoDias (relatórios).

---

### 3. Evidência real, não resumo

**Problema hoje:** Sub-agents às vezes retornam "Query executada com sucesso, 47 linhas retornadas" em vez do dado real. Perco visibilidade.

**Melhoria:** Padronizar que todo sub-agent que executa algo retorna:
- Output bruto (ou amostra se muito grande)
- Comando/query exato que rodou
- Status de erro se houver

**Onde aplicar:** Já funciona nos bridges (postgres_bridge, trino_bridge retornam dados). O gap está nos sub-agents que **resumem** antes de devolver — instruir para não resumir a evidência.

---

### 4. Budget de complexidade por delegação

**Problema hoje:** Posso pedir para um sub-agent fazer algo muito amplo (ex: "analise todas as tabelas e me diga quais têm dados inconsistentes"). Quanto mais amplo, mais chance de erro ou token explosion.

**Melhoria:** Regra interna: se a tarefa envolve >3 fontes de dados ou >5 ações distintas, quebrar em stages separados no pipeline do subagent.

**Onde aplicar:** Decisão minha na hora de montar o pipeline. Não é automático, é disciplina.

---

### 5. Gate de revisão antes de ações destrutivas em batch

**Problema hoje:** Se peço para o Jirinha criar 10 tasks ou mover 8 issues, ele executa tudo de uma vez. Se errou o template, são 10 tasks erradas.

**Melhoria:** Para operações batch (>3 itens), o agente deve:
1. Mostrar preview do primeiro item
2. Pedir confirmação
3. Só depois executar o batch

**Onde aplicar:** Steering do Jirinha e template de criação de tasks.

---

## O que NÃO faz sentido importar

- **Lifecycle completo com estados (RASCUNHO → APROVADO → etc.):** Nosso fluxo é conversacional e iterativo. Formalizar demais engessa sem ganho proporcional pro volume que operamos.
- **Spec como documento separado por feature:** Overhead alto para tasks pontuais. Faz sentido para projetos grandes, não para o dia-a-dia de produto.
- **Plano de testes formal na spec:** Não desenvolvemos software nesse fluxo — orquestramos dados, relatórios e gestão. Testes automatizados não se aplicam da mesma forma.

---

## Próximos passos

- [ ] Atualizar steering do Jirinha com regra de preview em batch
- [ ] Adicionar "Fora de escopo" nos prompts padrão de sub-agents
- [ ] Testar "Premissas assumidas" no Einstein por 1 semana e avaliar se melhora a qualidade
