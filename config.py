#!/usr/bin/env python3
'''
CONFIG — Monitor de Leilões de Motos
Centraliza todos os lotes, sites e parâmetros
'''

# ============================================================
# LOTES MONITORADOS
# ============================================================
# fase: 'discovery' | 'pre_leilao' | 'disputa' | 'encerrado'
# frequencia_check:
#   discovery/pre_leilao  → 1x ao dia (cron daily)
#   disputa               → a cada 15min (cron */15)
#   encerrado             → removido ou arquivado

LOTES = [
    {
        'id': '0054',
        'leilao': '5105',
        'leiloeiro': 'Prefeitura Vinhedo',
        'site': 'sumare',
        'modelo': 'Honda CG 160 Start',
        'ano': '24/24',
        'cor': 'Vermelho',
        'fase': 'pre_leilao',          # fase atual
        'url_lote': 'https://www.sumareleiloes.com.br/lotes/a2d784ba-42d8-4364-8d70-5df8f9a3e852',
        'url_leilao': 'https://www.sumareleiloes.com.br/leiloes/5105',
        'lance_inicial': 5800.0,
        'fipe': 16322.0,
        'preco_mercado_min': 16000.0,
        'preco_mercado_max': 19000.0,
        'incremento': 250.0,
        'comissao_pct': 5.0,
        'despesas': 1500.0,
        'data_abertura': '2026-05-08',
        'data_encerramento': None,    # a definir — buscado do site
        'notas': 'Melhor oportunidade do certame. Margem estimada R$8-11k.',
    },
    {
        'id': '0056',
        'leilao': '5105',
        'leiloeiro': 'Prefeitura Vinhedo',
        'site': 'sumare',
        'modelo': 'Honda CG 160 Fan',
        'ano': '21/21',
        'cor': 'Vermelho',
        'fase': 'pre_leilao',
        'url_lote': 'https://www.sumareleiloes.com.br/lotes/fb99a7d3-0cf9-43ac-b66b-e043e648e6cc',
        'url_leilao': 'https://www.sumareleiloes.com.br/leiloes/5105',
        'lance_inicial': 5150.0,
        'fipe': 14887.0,
        'preco_mercado_min': 13000.0,
        'preco_mercado_max': 17000.0,
        'incremento': 250.0,
        'comissao_pct': 5.0,
        'despesas': 1500.0,
        'data_abertura': '2026-05-08',
        'data_encerramento': None,
        'notas': '',
    },
    {
        'id': '0059',
        'leilao': '5105',
        'leiloeiro': 'Prefeitura Vinhedo',
        'site': 'sumare',
        'modelo': 'Shineray XY125-6A',
        'ano': '25/25',
        'cor': 'Branca',
        'fase': 'pre_leilao',
        'url_lote': 'https://www.sumareleiloes.com.br/lotes/89022928-cd28-4e3b-9c23-d913b0528975',
        'url_leilao': 'https://www.sumareleiloes.com.br/leiloes/5105',
        'lance_inicial': 3300.0,
        'fipe': 9012.0,
        'preco_mercado_min': 7000.0,
        'preco_mercado_max': 10000.0,
        'incremento': 150.0,
        'comissao_pct': 5.0,
        'despesas': 1500.0,
        'data_abertura': '2026-05-08',
        'data_encerramento': None,
        'notas': 'Shineray — marca com menos liquidez. Margem menor.',
    },
    {
        'id': '0065',
        'leilao': '5105',
        'leiloeiro': 'Prefeitura Vinhedo',
        'site': 'sumare',
        'modelo': 'Honda CG 160 Start',
        'ano': '23/23',
        'cor': 'Azul',
        'fase': 'pre_leilao',
        'url_lote': 'https://www.sumareleiloes.com.br/lotes/52c0f388-4e66-4855-af92-7aedd5cd26ae',
        'url_leilao': 'https://www.sumareleiloes.com.br/leiloes/5105',
        'lance_inicial': 5550.0,
        'fipe': 15558.0,
        'preco_mercado_min': 15000.0,
        'preco_mercado_max': 17000.0,
        'incremento': 250.0,
        'comissao_pct': 5.0,
        'despesas': 1500.0,
        'data_abertura': '2026-05-08',
        'data_encerramento': None,
        'notas': '',
    },
    # ——————————————————
    # NOVOS LOTES DO RELATÓRIO
    # Adicionar aqui conforme Lucas encontrar oportunidades
    # ——————————————————
    # {
    #     'id': '0012',
    #     'leilao': '2382',
    #     'leiloeiro': 'DETRAN Limeira/Paulínia',
    #     'site': 'sumare',
    #     'modelo': 'Honda CG 125 Fan ES',
    #     'ano': '13/13',
    #     'cor': 'Vermelho',
    #     'fase': 'pre_leilao',
    #     'url_lote': 'https://...',
    #     'url_leilao': 'https://www.sumareleiloes.com.br/leiloes/2382',
    #     'lance_inicial': 2300.0,
    #     'fipe': 13000.0,
    #     'preco_mercado_min': 11000.0,
    #     'preco_mercado_max': 14000.0,
    #     'incremento': 100.0,
    #     'comissao_pct': 5.0,
    #     'despesas': 1500.0,
    #     'data_abertura': '2026-05-07',
    #     'data_encerramento': '2026-05-14',
    #     'notas': 'Verificar se ainda está ativo — encerra 14/05',
    # },
]

# ============================================================
# SITES MONITORADOS (futuro — novos leiloeiros)
# ============================================================
SITES = {
    'sumare': {
        'nome': 'Sumaré Leilões',
        'url': 'https://www.sumareleiloes.com.br',
        'crawler': 'sumare',
        'tipo': 'prefeitura/detran',
    },
    'ricoleiloes': {
        'nome': 'Rico Leilões (EMDEC Campinas)',
        'url': 'https://www.ricoleiloes.com.br',
        'crawler': 'ricoleiloes',
        'tipo': 'patio_municipal',
    },
    'hastasp': {
        'nome': 'Hasta SP (Prefeitura SBC)',
        'url': 'https://www.hastasp.com.br',
        'crawler': 'hastasp',
        'tipo': 'prefeitura_infracao',
    },
}

# ============================================================
# REGRAS DE FREQUÊNCIA POR FASE
# ============================================================
PHASE_CONFIG = {
    'discovery': {
        'label': '🔍 Descoberta',
        'frequencia': 'daily',
        'cron': '0 9 * * *',         # 09h todo dia
        'descricao': 'Leilão ainda não abriu ou lote novo encontrado',
    },
    'pre_leilao': {
        'label': '📅 Pré-Leilão',
        'frequencia': 'daily',
        'cron': '0 9 * * *',
        'descricao': 'Lances pré-abertos, aguardando sessão',
    },
    'disputa': {
        'label': '🔥 Disputa',
        'frequencia': 'rapida',
        'cron': '*/15 * * * *',       # a cada 15 min só durante disputa
        'descricao': 'Leilão em andamento — acompanhar ritmo',
    },
    'encerrado': {
        'label': '✅ Encerrado',
        'frequencia': 'none',
        'cron': None,
        'descricao': 'Leilão encerrado — removido do monitoramento ativo',
    },
}

# ============================================================
# ALERTAS
# ============================================================
ALERTES = {
    'variacao_lance_pct': 15.0,      # alerta se lance subiu >X% vs último ciclo
    'margem_minima_pct': 30.0,       # alerta se margem caiu abaixo de X%
    'novo_lance': True,              # alerta quando qualquer lance novo aparece
    'encerramento_24h': True,        # alerta 24h antes do encerramento
}

# ============================================================
# CAMINHOS
# ============================================================
BASE_DIR = '/home/work/.openclaw/workspace/projects/leilao-monitor'
DATA_DIR = f'{BASE_DIR}/data'
STATE_FILE = f'{DATA_DIR}/state.json'
HISTORY_FILE = f'{DATA_DIR}/history.json'
LOG_FILE = f'{DATA_DIR}/monitor.log'
DASHBOARD_DIR = f'{BASE_DIR}/dashboard'