# Rotinas — LeoDias

## Localização dos scripts
- Pasta de rotinas: `/Users/thiago.dias/Documents/Main/Brain/Rotines/`
- Pasta de bridges: `/Users/thiago.dias/Documents/Main/Brain/Bridges/`
- Usar sempre essas pastas

## Rotinas cadastradas

| Script | Horário (cron) | Frequência | Banco | Output |
|--------|---------------|-----------|-------|--------|
| daily_vehicle_report.py | 12h00 e 18h00 | Todo dia | vehicle_history_production | Slack + CSV em ~/Documents/Vehicle Reports/ |
| weekly_safra_rejected_report.py | 10h30 | Toda segunda-feira | advertising_vas | Slack + CSV em ~/Documents/Safra Report Semanal/ |
| weekly_vas_report.py | 10h30 | Toda segunda-feira | advertising_vas | Slack + CSV em ~/Documents/Safra Report Semanal/ |
| sprint_confluence_watcher.py | 9h00 e 17h00 | Todo dia | — (Jira API) | Confluence + Slack ao detectar fim de sprint |
| daily_support_report.py | 11h00 | Todo dia | — (Jira API) | Confluence > Suportes (7225475077) |
| b3_veiculos_updater.py | 10h00 | Todo dia 15 | — (B3 website) | PDFs + textos em ~/Documents/B3-Financiamentos-Veiculos/ + knowledge base |
| base_queima_hv.py | — | Sob demanda | Trino (hive) | XLS em ~/Desktop/ |
| daily_brain_backup_drive.py | 10h30 | Todo dia | — (Google Drive API) | Pasta Brain → Drive (Backup_Thiago_Diario) + Slack |

## Logs
- daily_vehicle_report → /Users/thiago.dias/daily_vehicle_report.log
- weekly_safra_rejected_report → /Users/thiago.dias/weekly_safra_rejected_report.log
- weekly_vas_report → /Users/thiago.dias/weekly_vas_report.log
- sprint_confluence_watcher → /Users/thiago.dias/sprint_confluence_watcher.log
- daily_support_report → /Users/thiago.dias/daily_support_report.log

## Slack
- Canal principal: `C0B2X8FQ81M` (leo-dias-news)
- Token: `SLACK_BOT_TOKEN` em `~/Documents/Brain/.env`
- Toda notificação pós-execução é responsabilidade do agente **leodias**

## Notas
- Scripts verificam conectividade automaticamente e notificam o Slack em caso de falha de VPN
- Arquivos grandes são divididos automaticamente (>25 MB no safra_rejected, >50 MB no vas_report)
