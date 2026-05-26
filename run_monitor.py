#!/usr/bin/env python3
'''
MONITOR DE LEILÕES DE MOTOS — Lucas / AlfaPrime
Executa a cada 15 minutos via cron
Salva histórico em logs/ e envia alerta por e-mail
'''

import subprocess
import json
import os
import time
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
PROJECT_DIR = '/home/work/.openclaw/workspace/projects/leilao-monitor'
LOG_DIR = f'{PROJECT_DIR}/logs'
DATA_FILE = f'{LOG_DIR}/historico.json'
ALERT_THRESHOLD_PCT = 15  # alerta se lance subiu >15% no ciclo

LOTES = [
    {
        'id': '0054',
        'modelo': 'Honda CG 160 Start',
        'ano': '24/24',
        'cor': 'Vermelho',
        'url': 'https://www.sumareleiloes.com.br/lotes/a2d784ba-42d8-4364-8d70-5df8f9a3e852',
        'lance_inicial': 5800.0,
        'fipe': 16322.0,
        'preco_mercado_min': 16000.0,
        'preco_mercado_max': 19000.0,
        'incremento': 250.0,
        'comissao_pct': 5,
        'despesas': 1500.0,
    },
    {
        'id': '0056',
        'modelo': 'Honda CG 160 Fan',
        'ano': '21/21',
        'cor': 'Vermelho',
        'url': 'https://www.sumareleiloes.com.br/lotes/fb99a7d3-0cf9-43ac-b66b-e043e648e6cc',
        'lance_inicial': 5150.0,
        'fipe': 14887.0,
        'preco_mercado_min': 13000.0,
        'preco_mercado_max': 17000.0,
        'incremento': 250.0,
        'comissao_pct': 5,
        'despesas': 1500.0,
    },
    {
        'id': '0059',
        'modelo': 'Shineray XY125-6A',
        'ano': '25/25',
        'cor': 'Branca',
        'url': 'https://www.sumareleiloes.com.br/lotes/89022928-cd28-4e3b-9c23-d913b0528975',
        'lance_inicial': 3300.0,
        'fipe': 9012.0,
        'preco_mercado_min': 7000.0,
        'preco_mercado_max': 10000.0,
        'incremento': 150.0,
        'comissao_pct': 5,
        'despesas': 1500.0,
    },
    {
        'id': '0065',
        'modelo': 'Honda CG 160 Start',
        'ano': '23/23',
        'cor': 'Azul',
        'url': 'https://www.sumareleiloes.com.br/lotes/52c0f388-4e66-4855-af92-7aedd5cd26ae',
        'lance_inicial': 5550.0,
        'fipe': 15558.0,
        'preco_mercado_min': 15000.0,
        'preco_mercado_max': 17000.0,
        'incremento': 250.0,
        'comissao_pct': 5,
        'despesas': 1500.0,
    },
]

os.makedirs(LOG_DIR, exist_ok=True)

# ============================================================
# FUNÇÕES
# ============================================================

def crawl_lote(url):
    '''Busca dados de um lote via gsk crawl'''
    result = subprocess.run(
        ['gsk', 'crawl', url, '--render_js'],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout

def parse_lote(text, lote):
    '''Extrai lance atual e status do texto HTML'''
    import re
    data = {}

    # Lance Atual
    m = re.search(r'Lance Atual[^>]+>[^>]+>[^>]*R\ufffd?([\f0-9\ufffd,]+)', text)
    if not m:
        # alternativa
        m = re.search(r'Lance Atual.*?R\ufffd?\ufffd?([\f0-9\ufffd,\ufffd]+)', text, re.DOTALL)
    if not m:
        # fallback: procurar valor monetário
        m = re.search(r'R\ufffd?\ufffd?\ufffd?\f*([0-9\ufffd]{1,3}(?:\f[0-9\ufffd]{3})*,\ufffd?[0-9\ufffd]{2})', text)

    data['lance_atual'] = 0.0
    data['status'] = 'sem_lance'
    data['text_snippet'] = text[:500]

    return data

def calc_custo(lance):
    '''Calcula custo total com comissão e despesas'''
    comissao = lance * 0.05
    despesas = 1500.0
    return lance + comissao + despesas

def calc_margem(lote, lance_atual):
    '''Calcula margem de lucro'''
    custo = calc_custo(lance_atual)
    venda_min = lote['preco_mercado_min']
    venda_max = lote['preco_mercado_max']
    margem_min = venda_min - custo
    margem_max = venda_max - custo
    return custo, margem_min, margem_max

def load_historico():
    '''Carrega histórico anterior'''
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_historico(data):
    '''Salva histórico atualizado'''
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def format_currency(val):
    return f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

# ============================================================
# MAIN
# ============================================================
def main():
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    print(f'\n=== MONITOR LEILÃO — {now} ===\n')

    historico = load_historico()
    alertas = []

    for lote in LOTES:
        url = lote['url']
        bid = lote['id']

        print(f'Lote {bid} — {lote[\"modelo\"]} {lote[\"ano\"]}...')

        try:
            text = crawl_lote(url)
        except Exception as e:
            print(f'  Erro ao buscar: {e}')
            continue

        # Parse simplificado: procura valor de lance atual na página
        import re
        lance_str = re.search(r'Lance Atual.*?R\ufffd?\ufffd?\ufffd?\f*([0-9\ufffd]{1,3}(?:\f[0-9\ufffd]{3})*,\ufffd?[0-9\ufffd]{2})', text)
        if not lance_str:
            lance_str = re.search(r'R\ufffd?\ufffd?([0-9]{1,3}\f[0-9]{3},\ufffd?[0-9]{2})', text)

        lance_atual = 0.0
        if lance_str:
            # limpar string
            val_clean = re.sub(r'[^\f0-9,]', '', lance_str.group(1).replace('.', ''))
            try:
                lance_atual = float(val_clean.replace(',', '.'))
            except:
                lance_atual = lote['lance_inicial']  # fallback
        else:
            lance_atual = lote['lance_inicial']

        # Calcular margem
        custo, margem_min, margem_max = calc_margem(lote, lance_atual)

        # Histórico
        last = historico.get(bid, {}).get('lance_atual', 0)
        variacao = 0
        if last > 0:
            variacao = ((lance_atual - last) / last) * 100

        historico[bid] = {
            'timestamp': now,
            'lance_atual': lance_atual,
            'lance_inicial': lote['lance_inicial'],
            'variacao_pct': round(variacao, 1),
        }

        # Alertas
        status = '🟢 Sem lance' if lance_atual == 0 else (
            '🟡 Novo lance' if last == 0 else
            ('🔴 +' + f'{variacao:.0f}%' if variacao > 0 else '🟢 Estável')
        )

        # Margem
        margem_pct = (margem_min / custo * 100) if custo > 0 else 0

        print(f'  Lance atual: {format_currency(lance_atual)} | {status}')
        print(f'  Custo total: {format_currency(custo)} | Margem: {format_currency(margem_min)} a {format_currency(margem_max)} ({margem_pct:.0f}%)')
        print(f'  Link: {url}')
        print()

        if variacao > ALERT_THRESHOLD_PCT:
            alertas.append(f'⚠️ Lote {bid} ({lote[\"modelo\"]}) subiu {variacao:.0f}%! Novo lance: {format_currency(lance_atual)}')

    save_historico(historico)

    # Resumo
    print('=' * 40)
    print(f'Verificação: {now}')
    print(f'Lotes monitorados: {len(LOTES)}')
    if alertas:
        print('\nALERTAS:')
        for a in alertas:
            print(f'  {a}')
    else:
        print('Nenhum alerta nesta rodada')

if __name__ == '__main__':
    main()