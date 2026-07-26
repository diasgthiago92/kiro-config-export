# Memória Operacional — Erros conhecidos e lições aprendidas

## Propósito
Este arquivo registra erros que já aconteceram durante execução dos agentes, além de erros potenciais identificados por análise de código. Antes de executar uma tarefa, consultar se há lição relevante aqui para não repetir o mesmo erro.

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

### Batch sem preview pode causar dano em massa
- **Contexto:** Criar ou mover múltiplas issues de uma vez
- **Erro:** Issues criadas com dados errados ou movidas para status incorreto sem possibilidade de reverter facilmente
- **Causa:** Execução em lote sem passo de validação
- **Solução:** Para operações que afetam >3 itens, montar preview do primeiro, confirmar com o usuário, e só então executar o batch

### Scope creep — agente "melhora" coisas que não foram pedidas
- **Contexto:** Usuário pede para criar uma task; agente corrige descrição de outra issue
- **Erro:** Alterações não solicitadas em issues existentes
- **Causa:** Agente tenta ser proativo demais
- **Solução:** Executar APENAS o que foi solicitado. Se identificar algo adjacente que precisa atenção, reportar como observação — não agir

### Issue type inválido causa erro silencioso
- **Contexto:** Criar issue com tipo que não existe no projeto APRI
- **Erro:** API retorna erro genérico de campo obrigatório
- **Causa:** O nome do issue type precisa ser exatamente como está configurado no Jira (case-sensitive)
- **Solução:** Tipos válidos: História, Bug, Epic, Task, Discovery, Discovery Task, Hypothesis, Opportunity, Tech Value, Toil, Support, Technical Debt

### Assignee não encontrado quando email errado
- **Contexto:** Criar/atribuir issue com email de pessoa que saiu do time
- **Erro:** API retorna lista vazia no user search; issue fica sem assignee sem avisar
- **Causa:** `atlassian_bridge.py` busca usuário mas não levanta erro quando não encontra — simplesmente omite o campo
- **Solução:** Verificar que o email está na lista do time antes de atribuir. Se não encontrar, informar o usuário

---

## Trino/Hive

### Queries grandes precisam de LIMIT
- **Contexto:** SELECT * em tabela do ODS sem LIMIT
- **Erro:** Timeout ou retorno de dados gigante que estoura contexto
- **Causa:** Tabelas ODS têm milhões de linhas
- **Solução:** Sempre usar LIMIT (padrão: 100) em queries exploratórias. Só remover quando o usuário pedir explicitamente

### Parsing frágil com ast.literal_eval
- **Contexto:** `base_queima_hv.py` parseia resposta do bridge Trino
- **Erro:** `SyntaxError` ou `ValueError` quando dados contêm caracteres especiais (aspas, newlines, backslashes em campos text)
- **Causa:** O bridge retorna dados como string Python repr (`Colunas: [...]\nDados: [...]`) e o parser usa `ast.literal_eval`, que é frágil para texto livre
- **Solução:** Se a query retorna campos de texto livre, verificar se o parse funcionou. Em caso de erro, considerar limitar colunas retornadas ou usar apenas colunas numéricas/date. Alternativa futura: migrar retorno do bridge para JSON nativo

### Timeout não configurado no bridge Trino
- **Contexto:** Queries pesadas no Trino (joins de tabelas grandes no ODS)
- **Erro:** Processo fica pendurado indefinidamente sem feedback
- **Causa:** `trino_mcp_bridge.py` não define timeout na conexão nem no cursor
- **Solução:** Rotinas que usam o bridge devem definir timeout no `subprocess.run` (como `base_queima_hv.py` faz com `timeout=1800`). Para uso interativo, considerar timeout de 300s

### Schema não especificado causa "table not found"
- **Contexto:** Executar query sem prefixar com `hive.ods.`
- **Erro:** "Table 'tabela' does not exist"
- **Causa:** O bridge usa schema padrão `ods`, mas tabelas em outros schemas (olx_auto, olx_vas_premium) precisam de qualificação completa
- **Solução:** Sempre usar nome completo: `hive.schema.tabela`. Schemas conhecidos: `ods`, `olx_auto`, `olx_vas_premium`

### VPN obrigatória para conectar — sem retry automático
- **Contexto:** Executar query Trino com VPN desconectada
- **Erro:** Connection refused / timeout sem mensagem clara
- **Causa:** O gateway Trino só é acessível via VPN corporativa
- **Solução:** Verificar conectividade antes (`nc -z -w3 trino-gateway.dataeng.bigdata.olxbr.io 443`). Se falhar, avisar o usuário para conectar VPN

---

## PostgreSQL

### VPN obrigatória — falha silenciosa se desconectada
- **Contexto:** Query em qualquer banco PostgreSQL (advertising_vas, vehicle_history_production)
- **Erro:** `psycopg2.OperationalError: could not connect to server`
- **Causa:** Bancos internos só acessíveis via VPN
- **Solução:** Verificar conectividade antes da query: `nc -z -w3 <host> 5432`. Se falhar, abrir FortiClient e avisar o usuário

### Conexão não fechada em caso de exceção no bridge
- **Contexto:** Query falha (sintaxe SQL errada, tabela inexistente) no `postgres_bridge.py`
- **Erro:** Conexões ficam abertas (pool exhaustion em uso intenso)
- **Causa:** O bridge fecha `conn` no happy path, mas se `cur.execute()` falhar dentro do bloco `tools/call`, a exceção é capturada pelo `except` externo e a conexão não é fechada
- **Solução:** Mitigação: evitar queries em sequência rápida sem intervalo. Futuro: refatorar com `try/finally` ou context manager

### Senha vazia ou placeholder no .env
- **Contexto:** Primeiro uso após reinstalação ou novo perfil
- **Erro:** Bridge retorna "ERRO: Senha para o perfil 'X' não configurada"
- **Causa:** `.env` tem placeholder `SUA_SENHA_AQUI` ou campo vazio
- **Solução:** Verificar se o bridge retorna erro de senha antes de assumir que há problema de rede

### Profile errado → banco errado
- **Contexto:** Querer consultar `vehicle_histories` mas esquecer `profile="vehicle_history"`
- **Erro:** "relation does not exist" (porque consulta no advertising_vas que não tem essa tabela)
- **Causa:** Profile default é `advertising_vas`; tabelas de veículo estão em outro perfil
- **Solução:** Tabelas `vehicle_histories*` → profile `vehicle_history`. Tabelas `financing_*`, `safra_*`, `vas_*` → profile `default`

---

## Google/Drive

### OAuth2 falha em cron (Gmail/Slides)
- **Contexto:** Rotina agendada tenta usar Gmail ou Slides
- **Erro:** `InstalledAppFlow.run_local_server` fica pendurado esperando browser que nunca abre
- **Causa:** OAuth2 para Gmail/Slides requer interação de browser na primeira vez E quando token expira
- **Solução:** Gmail/Slides não devem ser usados em rotinas automatizadas (cron). Usar apenas interativamente. Drive/Sheets usam Service Account e funcionam sem browser

### Token OAuth2 expirado sem refresh_token
- **Contexto:** Usar Gmail após muito tempo sem uso
- **Erro:** Erro de autenticação; bridge tenta abrir browser
- **Causa:** Token em `~/.kiro/google_token.json` expirou e não tem `refresh_token` (ou o refresh_token expirou)
- **Solução:** Deletar `~/.kiro/google_token.json` e reautorizar manualmente: `python3 google_bridge.py` com um payload de teste

### Service Account sem acesso a arquivo pessoal
- **Contexto:** Tentar ler arquivo do Drive pessoal via bridge
- **Erro:** 404 Not Found ou "File not found"
- **Causa:** Service Account é uma identidade separada; não tem acesso a arquivos do Drive pessoal
- **Solução:** Compartilhar o arquivo/pasta com `kiro-cli-sa@kiro-cli-vas-tools.iam.gserviceaccount.com` antes de acessar

### Backup diário não limpa backups antigos
- **Contexto:** `daily_brain_backup_drive.py` executa todo dia
- **Erro:** Acúmulo de centenas de pastas `Brain_YYYY-MM-DD` no Drive sem cleanup
- **Causa:** Script só cria pasta e faz upload; não remove backups anteriores
- **Solução:** Atenção: verificar espaço no Drive periodicamente. Futuro: implementar retenção (manter últimos 7 dias, por exemplo)

### Upload falha com arquivos >5MB sem resumable
- **Contexto:** Backup do Brain com arquivos grandes (logs, XLS exportados)
- **Erro:** Timeout no upload
- **Causa:** `MediaFileUpload` está com `resumable=True` (correto), mas se a rede oscilar, o retry pode não ser suficiente
- **Solução:** O script já tem `retries=3`. Se persistir, verificar se o arquivo não é um symlink quebrado (o script já trata isso)

---

## Slack

### Token inválido ou expirado
- **Contexto:** Enviar mensagem pelo bridge
- **Erro:** `{"ok": false, "error": "invalid_auth"}`
- **Causa:** Bot token em `.env` expirou ou foi revogado
- **Solução:** Gerar novo token em https://api.slack.com/apps e atualizar `SLACK_BOT_TOKEN` no `.env`

### Canal inválido não gera erro claro
- **Contexto:** Enviar mensagem para canal ID errado
- **Erro:** `{"ok": false, "error": "channel_not_found"}` — mas a rotina que chama pode não tratar
- **Causa:** `slack_bridge.py` retorna "❌ Erro: channel_not_found" mas rotinas que chamam `send_slack_message()` fazem `json.loads(result.stdout)` sem verificar se deu erro
- **Solução:** Sempre verificar que a mensagem foi enviada. Se não foi, logar o erro mas não travar a rotina

### Mensagem muito longa é truncada silenciosamente
- **Contexto:** Enviar relatório completo como mensagem Slack
- **Erro:** Mensagem aparece cortada no Slack
- **Causa:** Slack tem limite de ~4000 caracteres por mensagem
- **Solução:** Para relatórios grandes, dividir em múltiplas mensagens ou enviar arquivo/link

### Rate limit do Slack (1 msg/segundo por canal)
- **Contexto:** Enviar mensagens em loop para múltiplos canais (ex: lista "Pausa para o Café")
- **Erro:** Slack retorna `error: rate_limited` após ~20 mensagens rápidas
- **Causa:** Bridge não tem delay entre envios
- **Solução:** Adicionar `time.sleep(1.5)` entre envios em loops. Para listas grandes, considerar 2s de intervalo

---

## Rotinas (LeoDias)

### VPN caiu no meio da execução
- **Contexto:** Rotina começa com VPN ok, mas desconecta durante a query
- **Erro:** `psycopg2.OperationalError: server closed the connection unexpectedly`
- **Causa:** VPN instável desconecta durante transferência de dados
- **Solução:** Scripts verificam no início, mas não no meio. Se falhar, a mensagem de erro vai para o Slack. Futuro: implementar retry com backoff

### Arquivo CSV gerado vazio (0 linhas)
- **Contexto:** Relatório semanal ou diário sem dados
- **Erro:** Arquivo CSV criado com apenas header; mensagem de sucesso enviada ao Slack
- **Causa:** Query retorna 0 linhas (ex: período sem dados, tabela vazia, filtro muito restritivo)
- **Solução:** Verificar `len(df) > 0` antes de salvar. Se vazio, enviar alerta diferente ao Slack ("atenção: sem dados no período")

### Sprint watcher detecta sprint já publicada
- **Contexto:** `sprint_confluence_watcher.py` roda 2x/dia
- **Erro:** Duplicação de página no Confluence (raro mas possível)
- **Causa:** Se o state file (`sprint_confluence_watcher.state`) for corrompido ou deletado, o script tenta republicar sprints antigas
- **Solução:** Script já verifica por título no Confluence antes de criar (busca + update se existir). Se state file sumir, ele republicará mas atualizará ao invés de duplicar

### Sprint watcher usa `requests` diretamente (inconsistência)
- **Contexto:** `get_closed_sprints()` em `sprint_confluence_watcher.py`
- **Erro:** Potencial — se credenciais mudarem no `.env`, esta função pode usar valores diferentes do bridge Atlassian
- **Causa:** `get_closed_sprints` faz HTTP direto com `requests` em vez de usar o `atlassian_bridge.py`; o resto do script usa o bridge
- **Solução:** Atenção se mudar credenciais. Os dois caminhos (requests direto e bridge) leem o mesmo `.env`, mas um bug em um pode não afetar o outro

### Cron não herda PATH — dependências não encontradas
- **Contexto:** Rotina falha no cron mas funciona manualmente
- **Erro:** `ModuleNotFoundError: No module named 'pandas'` (ou similar)
- **Causa:** Cron usa PATH mínimo (`/usr/bin:/bin`); `pip install` coloca em `/opt/homebrew/lib/python3.x/`
- **Solução:** Usar caminho absoluto do Python no cron: `/usr/bin/python3` ou `/opt/homebrew/bin/python3`. Verificar que o venv ou site-packages está acessível

### daily_brain_backup_drive — symlinks quebrados
- **Contexto:** Backup tenta enviar arquivo que é symlink para local inexistente
- **Erro:** O script já trata (`resolve()` + `exists()` check), mas um symlink para fora do Brain pode causar upload de arquivo externo
- **Causa:** Symlinks em `~/Documents/Main/Brain` apontando para outros locais
- **Solução:** Script já pula symlinks quebrados com warning. Para symlinks válidos, verifica e faz upload do target

---

## Agente em Geral (Cross-cutting)

### Análise genérica quando falta direction
- **Contexto:** Pedir ao Einstein "analise essa tabela" sem especificar o quê
- **Erro:** Resposta vaga, superficial, ou focando em aspecto irrelevante
- **Causa:** Sem decision points nomeados, o agente escolhe o que achar mais "interessante"
- **Solução:** Sempre incluir perguntas específicas: "Volume mudou? Há concentração? Taxa de erro ok?"

### Output grande estoura contexto do LLM
- **Contexto:** Query retorna muitos dados que são incluídos na resposta
- **Erro:** Contexto window esgotado; resposta truncada ou agente perde informação anterior
- **Causa:** Não limitar output de queries ou usar representação compacta
- **Solução:** Usar RTK para comprimir outputs. Limitar queries com LIMIT. Para relatórios grandes, salvar em arquivo e retornar apenas resumo

### Modelo pesado para task mecânica (custo desnecessário)
- **Contexto:** Usar Sonnet para mover uma issue no Jira ou listar páginas
- **Erro:** Não é erro funcional, mas desperdício de tokens/custo
- **Causa:** Sem regra de routing de modelo por complexidade
- **Solução:** Task mecânica (mover issue, listar, formatar) → Haiku. Task analítica → Sonnet. Task padrão → Default

### Premissas não declaradas
- **Contexto:** Agente infere quarter atual, sprint ativa, ou assignee padrão
- **Erro:** Decisão incorreta que o usuário não percebe até ver o resultado
- **Causa:** Agente decide silenciosamente sem informar
- **Solução:** Sempre declarar premissas assumidas no output: "Premissa: usei Q3 2026 porque é o quarter atual"

---

## Infraestrutura / Ambiente

### FortiClient VPN desconecta aleatoriamente
- **Contexto:** Qualquer operação que depende de rede interna
- **Erro:** Conexão recusada ou timeout sem aviso
- **Causa:** VPN instável (idle timeout, mudança de rede Wi-Fi)
- **Solução:** Check obrigatório antes de cada sessão (`nc -z -w3 <host> <port>`). Se `VPN_OFF`, abrir FortiClient e aguardar

### .env com valor antigo após rotação de credenciais
- **Contexto:** Senha de banco ou token expirou/foi rotacionado
- **Erro:** Autenticação falha em todos os bridges que usam aquela credencial
- **Causa:** `~/Documents/Main/Brain/.env` não atualizado após rotação
- **Solução:** Se múltiplos bridges falham com "auth error", verificar .env primeiro. Credenciais sensíveis: POSTGRES_PASSWORD, POSTGRES_PASSWORD_VEHICLE, ATLASSIAN_TOKEN, SLACK_BOT_TOKEN

### Python packages desatualizados
- **Contexto:** Bridge falha com erro de API inesperado
- **Erro:** Mudança na API do Jira/Confluence/Google que quebra o bridge
- **Causa:** Dependências (requests, google-api-python-client, psycopg2) desatualizadas
- **Solução:** Manter dependências atualizadas. Se um bridge parar de funcionar após meses sem alteração, verificar changelog da API
