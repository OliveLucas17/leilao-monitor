#!/bin/bash
# ============================================================
# SISTEMA DE MONITORAMENTO DE LEILÕES DE MOTOS
# Lucas Oliveira / AlfaPrime
# ============================================================

LEILAO_URLS=(
    'https://www.sumareleiloes.com.br/lotes/a2d784ba-42d8-4364-8d70-5df8f9a3e852'
    'https://www.sumareleiloes.com.br/lotes/fb99a7d3-0cf9-43ac-b66b-e043e648e6cc'
    'https://www.sumareleiloes.com.br/lotes/89022928-cd28-4e3b-9c23-d913b0528975'
    'https://www.sumareleiloes.com.br/lotes/52c0f388-4e66-4855-af92-7aedd5cd26ae'
)

LOG_DIR='/home/work/.openclaw/workspace/projects/leilao-monitor/logs'
mkdir -p $LOG_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE=$LOG_DIR/status_$TIMESTAMP.json

# ============================================================
# FUNÇÃO: extrair dados de cada lote
# ============================================================
fetch_lote() {
    local URL=$1
    local ID=$(basename $URL)
    local TMP=$(mktemp)
    
    # Usa gsk crawl com render JS
    gsk crawl $URL --render_js 2>/dev/null > $TMP
    
    # Extrai informações-chave
    local LOTE=$(grep -oP 'Lote \\d+' $TMP | head -1 | grep -oP '\f+')
    local MODELO=$(grep -oP '(HONDA|YAMAHA|SHINERAY|BIZ|IMPERIAL)[^<]+' $TMP | head -1)
    local LANCE_INICIAL=$(grep -oP 'Lance Inicial:[^<]+<[^>]+>[^<]+' $TMP | grep -oP 'R\fd+[\f,]+')
    local LANCE_ATUAL=$(grep -oP 'Lance Atual:[^<]+<[^>]+>[^<]+' $TMP | grep -oP 'R\fd+[\f,]+')
    local DATA=$(date +%d/%m/%Y %H:%M)
    
    rm $TMP
}

# ============================================================
# MAIN: roda a cada verificação
# ============================================================
echo '{'
echo '  \"timestamp\": \"'$(date -Iseconds)'\",'
echo '  \"leiloes\": ['

FIRST=true
for URL in ${LEILAO_URLS[@]}; do
    echo '    {
      \"url\": \"'$URL'\",
      \"fetched\": \"$(date -Iseconds)\"
    }'
done

echo '  ]'
echo '}' > $LOG_FILE

echo '[OK] Verificação concluída em '$(date)'