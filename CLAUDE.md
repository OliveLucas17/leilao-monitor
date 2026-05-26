# CLAUDE.md — Contexto para o Claude Code

## Projeto
Monitor de leilões de motos para a AlfaPrime Transportes (Lucas Oliveira).
Repo: https://github.com/OliveLucas17/leilao-monitor

## Contexto do Negócio
- Lucas compra motos em leilõesonline (Sumaré, Ricoleiloes, Hasta SP)
- Filtro atual: **SEM Honda, Yamaha, Shineray** — só outras marcas (Dafra, Kawasaki, BMW, Suzuki, Kasinski, KTM, etc.)
- Só interessa **COM DIREITO A DOCUMENTO / PARA CIRCULAR**
- Negócio: locação de motos B2B (Empresas como Ambev, iFood) + pessoa física
- Margem esperada: acima de R$ 3.000 por moto revendida

## Plataformas Confiáveis
- **sumareleiloes.com.br** — Prefeitura de Vinhedo/Campinas (mesma plataforma)
- **ricoleiloes.com.br** — EMDEC Campinas (municipal, confiável)
- **hastasp.com.br** — Prefeitura São Bernardo do Campo

## Arquitetura Atual
- `config.py` — lotes monitorados + sites + thresholds de frequência
- `phases.py` — detecção de fase: discovery → pre_leilao → disputa → encerramento
- `monitor.py` — orchestration + geração do dashboard HTML
- `crawlers/` — um arquivo por plataforma (sumare.py OK, ricard.py e hastasp.py são placeholders)
- `data/state.json` — estado atual dos lotes (fase, último lance, último check)
- `data/history.json` — histórico de verificações
- `run_check.py` + `run.sh` — wrapper inteligente: se algum lote em `disputa`, roda a cada 15min; caso contrário só 1x ao dia

## Frequência por fase
- `discovery`/`pre_leilao` → 1x ao dia (evita spam de requests)
- `disputa` → a cada 15min (lote em guerra de lances)
- `encerrado` → para de monitorar

## Dashboard
- Gerado por `monitor.py` → serve em `/var/www/leilao-monitor/` → proxy em `/leilao` via Caddy
- Dashboard URL: `https://lucas170804-2e459368-5214-vm.azure.gensparkclaw.com/leilao/`
- Atualização: cron a cada 15min (via run.sh)

## Dados dos lotes atuais
| Lote | Modelo | Ano | Leilao | Fase |
|------|--------|-----|--------|------|
| 0054 | Honda CG 160 Start | 24/24 | 5105 (Vinhedo) | pre_leilao |
| 0056 | Honda CG 160 Fan | 21/21 | 5105 (Vinhedo) | pre_leilao |
| 0059 | Shineray XY125-6A | 25/25 | 5105 (Vinhedo) | pre_leilao |
| 0065 | Honda CG 160 Start | 23/23 | 5105 (Vinhedo) | pre_leilao |

⚠️ Todos são Honda/Shineray — Lucas exclui essas marcas. Precisava adicionar lotes de outras marcas conforme novos leilões abrem.

## Bugs conhecidos / TO-DO
1. crawlers/ricard.py e crawlers/hastasp.py são placeholders — precisam ser implementados
2. Ricoleiloes tem paginação em JS — crawler atual não detecta os lotes corretamente
3. Sistema de alertas (WhatsApp/email) ainda não implementado
4. Dashboard só atualiza quando monitor.py roda — não há notificação pro Lucas

## Como fazer deploy de mudanças
```bash
git add . && git commit -m 'descrição' && git push
# VM faz: cd ~/projects/leilao-monitor && git pull
```

## VM de produção
- SSH: work@lucas170804-2e459368-5214-vm.azure.gensparkclaw.com
- Cron: `*/15 * * * * cd ~/projects/leilao-monitor && python3 run_check.py`
- Pasta: `/home/work/.openclaw/workspace/projects/leilao-monitor/`

## Pastas敏感
- `data/state.json` — estado do monitor (não alterar manualmente)
- `data/history.json` — histórico (append only)