# 🚀 Leilao Monitor — AlfaPrime

Monitor inteligente de leilões de motos para a AlfaPrime Transportes.

## Stack
- Python 3 + Bash (cron wrapper)
- Crawlers modulares (Sumaré, Ricoleiloes, Hasta SP)
- Dashboard HTML com auto-refresh
- Estado em JSON (state.json / history.json)

## Estrutura
```
leilao-monitor/
├── config.py          # Lotes, sites, thresholds
├── phases.py          # Detecção de fase
├── monitor.py         # Orchestration + dashboard generator
├── run_check.py       # Wrapper inteligente (daily vs rápida)
├── run.sh             # Entry-point do cron
├── crawlers/          # Crawlers por plataforma
│   ├── sumare.py
│   ├── ricard.py
│   └── hastasp.py
├── data/              # Estado e logs
│   ├── state.json
│   └── history.json
└── dashboard/         # HTML do dashboard
```

## Dashboard (24/7 na VM)
http://lucashmlk.no.vc:8080

## Modo de uso
```bash
# Rodar manualmente
cd leilao-monitor && python3 monitor.py

# Ou via wrapper inteligente
bash run.sh
```

## Workflow: Claude Code → VM
1. Claude Code commita melhorias no repo
2. VM faz `git pull` (cron ou manual)
3. Monitor continua rodando 24/7

## Configurar novo lote
Edite `config.py` → array `LOTES`. Adicione:
```python
{
    'id': 'XXXX',
    'leilao': 'ID',
    'site': 'sumare',  # ou 'ricard', 'hastasp'
    'modelo': '...',
    'fase': 'discovery',
    'url_lote': 'https://...',
    ...
}
```