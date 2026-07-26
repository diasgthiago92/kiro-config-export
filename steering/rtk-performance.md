# RTK Performance

## Ver economia

Quando o usuário pedir para ver o "status de performance do rtk" ou "rtk gain", executar:

```bash
/opt/homebrew/bin/rtk gain
```

E exibir o output formatado mostrando tokens economizados, comandos usados e eficiência.

## Regra obrigatória — Usar RTK em TODOS os comandos shell suportados

O ambiente de execução do Kiro CLI (tool `shell`) **não herda o PATH do `.zshrc`**, então os wrappers em `~/bin/rtk-wrappers/` não são encontrados automaticamente.

**Path do RTK:** `/opt/homebrew/bin/rtk`

**Sempre prefixar com `rtk` os seguintes comandos:**

| Em vez de | Usar |
|-----------|------|
| `git ...` | `rtk git ...` |
| `grep ...` | `rtk grep ...` |
| `ls ...` | `rtk ls ...` |
| `tree ...` | `rtk tree ...` |
| `find ...` | `rtk find ...` |
| `diff ...` | `rtk diff ...` |
| `curl ...` | `rtk curl ...` |
| `docker ...` | `rtk docker ...` |
| `aws ...` | `rtk aws ...` |
| `gh ...` | `rtk gh ...` |
| `glab ...` | `rtk glab ...` |
| `psql ...` | `rtk psql ...` |
| `pnpm ...` | `rtk pnpm ...` |
| `npm run ...` | `rtk npm run ...` |
| `npx ...` | `rtk npx ...` |
| `kubectl ...` | `rtk kubectl ...` |
| `cargo ...` | `rtk cargo ...` |
| `dotnet ...` | `rtk dotnet ...` |
| `jest ...` | `rtk jest ...` |
| `vitest ...` | `rtk vitest ...` |
| `prisma ...` | `rtk prisma ...` |
| `tsc ...` | `rtk tsc ...` |
| `next build ...` | `rtk next ...` |
| `eslint ...` | `rtk lint ...` |
| `prettier ...` | `rtk prettier ...` |
| `playwright ...` | `rtk playwright ...` |
| `wget ...` | `rtk wget ...` |
| `wc ...` | `rtk wc ...` |

## Comandos especiais RTK (sem equivalente direto)

| Comando | Quando usar |
|---------|-------------|
| `rtk err <comando>` | Quando só preciso ver erros/warnings de qualquer comando |
| `rtk test <comando>` | Quando rodando testes e só preciso ver falhas |
| `rtk summary <comando>` | Quando preciso de resumo heurístico de output grande |
| `rtk json <arquivo>` | Para inspecionar JSON de forma compacta |
| `rtk json --keys-only <arquivo>` | Para ver só a estrutura/chaves de um JSON |
| `rtk log <arquivo>` | Para filtrar/deduplicar logs |
| `rtk deps` | Para resumir dependências de um projeto |
| `rtk env` | Para ver variáveis de ambiente (com masking de sensíveis) |
| `rtk read <arquivo>` | Para ler arquivo com filtro inteligente |

## Regras de decisão para maximizar economia

### Prioridade 1: Usar variante especializada quando existir
- Testes → `rtk test <cmd>` ou `rtk jest/vitest` (só mostra falhas)
- Build com erros → `rtk err <cmd>` (só mostra erros)
- Git log → `rtk git log` (output compactado)
- Git diff → `rtk diff` (ultra-condensado)

### Prioridade 2: Usar `rtk summary` para outputs muito grandes
- Quando o output esperado é >100 linhas e só preciso de visão geral
- Ex: `rtk summary docker ps -a`, `rtk summary kubectl get pods`

### Prioridade 3: Combinar com flags nativas de limite
- `rtk git log -10` (já compacta + limita)
- `rtk grep -l` quando só preciso de nomes de arquivo

## Exceções (NÃO usar rtk)

- `python3`, `python`, `pip` — RTK não suporta
- `cp`, `mv`, `rm`, `mkdir`, `chmod`, `chown` — operações de filesystem simples
- `cat`, `echo`, `printf`, `head`, `tail` — output já mínimo
- `cd`, `pwd`, `which`, `whoami` — output trivial
- `nc`, `open`, `pbcopy`, `pbpaste` — utilitários do sistema
- `brew`, `apt`, `dnf` — package managers (exceto se suportado no futuro)
- Quando o output precisa ser parseado como JSON puro (rtk pode alterar formatação)
- Quando o comando é interno de um pipeline complexo onde a compressão atrapalharia
- Quando o comando é passado como argumento para outro programa (ex: subprocess em Python)
