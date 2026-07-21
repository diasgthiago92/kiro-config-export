# Rotinas — LeoDias

## Localização dos scripts
- Pasta de rotinas: `~/Documents/Main/Brain/Rotines/`
- Pasta de bridges: `~/Documents/Main/Brain/Bridges/`
- Usar sempre essas pastas

## [CONFIGURAR] — Rotinas cadastradas

| Script | Horário (cron) | Frequência | Banco | Output |
|--------|---------------|-----------|-------|--------|
| (script_1.py) | (horário) | (frequência) | (banco) | (destino) |
| (script_2.py) | (horário) | (frequência) | (banco) | (destino) |

## Slack
- Canal principal: `[SLACK_CHANNEL_ID]`
- Token: `SLACK_BOT_TOKEN` em `~/Documents/Brain/.env`
- Toda notificação pós-execução é responsabilidade do agente **leodias**

## Notas
- Scripts verificam conectividade automaticamente e notificam o Slack em caso de falha de VPN
- Arquivos grandes são divididos automaticamente (definir threshold por script)
