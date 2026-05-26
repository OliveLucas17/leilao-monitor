#!/usr/bin/env python3
import os, sys, json, subprocess
from datetime import datetime
from config import (
    LOTES, PHASE_CONFIG, ALERTES, BASE_DIR, DATA_DIR,
    STATE_FILE, HISTORY_FILE, LOG_FILE
)
from phases import detectar_fase, precisa_verificar

os.makedirs(DATA_DIR, exist_ok=True)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_history(history):
    history = history[-500:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2, default=str)

def calc_custo(lance, lote):
    comissao = lance * (lote.get('comissao_pct', 5.0) / 100.0)
    despesas = lote.get('despesas', 1500.0)
    return lance + comissao + despesas

def calc_margens(lote, lance_atual):
    custo = calc_custo(lance_atual, lote)
    venda_min = lote.get('preco_mercado_min', 0)
    venda_max = lote.get('preco_mercado_max', 0)
    margem_min = venda_min - custo
    margem_max = venda_max - custo
    margem_pct = (margem_min / custo * 100.0) if custo > 0 else 0
    score = min(10.0, max(0.0, margem_pct / 15.0))
    return custo, margem_min, margem_max, margem_pct, score

def format_currency(val):
    return 'R$ ' + ('%.2f' % val).replace('.', ',')

def log_msg(msg):
    now = datetime.now().strftime('%d/%m %H:%M')
    line = '[' + now + '] ' + msg
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def detectar_fase_do_estado(lote, estado):
    status = str(estado.get('status', '')).lower()
    if status in ('encerrado', 'vendido'):
        return 'encerrado', {}
    data_fim_str = estado.get('data_encerramento') or lote.get('data_encerramento')
    data_fim = None
    if data_fim_str:
        for fmt in ['%d %b %Y %H:%M', '%Y-%m-%d', '%d/%m/%Y']:
            try:
                data_fim = datetime.strptime(data_fim_str.strip(), fmt)
                break
            except:
                continue
    hoje = datetime.now()
    lance_atual = estado.get('lance_atual', 0)
    if data_fim:
        delta = (data_fim - hoje).total_seconds() / 3600.0
        if delta < 0:
            return 'encerrado', {}
        elif delta < 24 or lance_atual > 0:
            return 'disputa', {'horas_restantes': round(delta, 1)}
        else:
            return 'pre_leilao', {'horas_restantes': round(delta, 1)}
    if lance_atual > 0 and lance_atual > lote.get('lance_inicial', 0):
        return 'pre_leilao', {'tem_lance': True}
    return lote.get('fase', 'pre_leilao'), {}

def run_check_lote(lote, state_atual):
    from crawlers import crawl
    lote_id = str(lote['id'])
    estado = state_atual.get(lote_id, {})
    last_check = estado.get('last_check', None)
    if last_check:
        try:
            last_dt = datetime.fromisoformat(last_check)
            horas = (datetime.now() - last_dt).total_seconds() / 3600.0
            fase = detectar_fase_do_estado(lote, estado)[0]
            if not precisa_verificar(fase, horas):
                log_msg('  ' + lote_id + ': pulou (fase=' + fase + ', ' + ('%.1f' % horas) + 'h desde ultimo)')
                return state_atual, None
        except:
            pass
    log_msg('  ' + lote_id + ': verificando...')
    try:
        dados = crawl(lote)
    except Exception as e:
        log_msg('  ' + lote_id + ': ERRO -> ' + str(e))
        estado['erro'] = str(e)
        estado['last_check'] = datetime.now().isoformat()
        state_atual[lote_id] = estado
        return state_atual, None
    estado.update({
        'lance_atual': dados.get('lance_atual', 0),
        'lance_inicial': lote.get('lance_inicial', 0),
        'status': dados.get('status', 'desconhecido'),
        'data_encerramento': dados.get('data_encerramento'),
        'html_snippet': dados.get('html_snippet', '')[:500],
        'last_check': datetime.now().isoformat(),
        'lance_anterior': estado.get('lance_atual', 0),
    })
    state_atual[lote_id] = estado
    return state_atual, estado

def checar_alertas(lote, estado_atual, estado_anterior):
    alertas = []
    if not estado_anterior:
        return alertas
    lance_atual = estado_atual.get('lance_atual', 0)
    lance_anterior = estado_anterior.get('lance_atual', 0)
    if lance_anterior > 0 and lance_atual > lance_anterior:
        var_pct = ((lance_atual - lance_anterior) / lance_anterior) * 100.0
        if var_pct >= ALERTES['variacao_lance_pct']:
            modelo_txt = str(lote.get('modelo') or '') + ' ' + str(lote.get('ano') or '')
            alertas.append({
                'tipo': 'variacao',
                'lote': str(lote['id']),
                'modelo': modelo_txt,
                'var_pct': round(var_pct, 1),
                'lance_anterior': lance_anterior,
                'lance_atual': lance_atual,
                'msg': 'ATENCAO ' + str(lote['id']) + ' subiu ' + str(int(var_pct)) + 'pct: ' + format_currency(lance_anterior) + ' -> ' + format_currency(lance_atual),
            })
    if ALERTES['novo_lance'] and lance_atual > 0 and lance_anterior == 0:
        modelo_txt = str(lote.get('modelo') or '') + ' ' + str(lote.get('ano') or '')
        alertas.append({
            'tipo': 'novo_lance',
            'lote': str(lote['id']),
            'modelo': modelo_txt,
            'lance_atual': lance_atual,
            'msg': 'NOVO LANCE ' + str(lote['id']) + ' (' + modelo_txt + '): ' + format_currency(lance_atual),
        })
    return alertas

def _html_escape(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('>', '&gt;')

def gerar_dashboard(state):
    now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    fases_count = {'discovery': 0, 'pre_leilao': 0, 'disputa': 0, 'encerrado': 0}
    for lote in LOTES:
        sid = str(lote['id'])
        est = state.get(sid, {})
        f = est.get('fase', lote.get('fase', 'pre_leilao'))
        fases_count[f] = fases_count.get(f, 0) + 1

    fase_colors = {
        'disputa': ('#ff6b35', '#fff8f4'),
        'pre_leilao': ('#3b82f6', '#eff6ff'),
        'discovery': ('#8b5cf6', '#f5f3ff'),
        'encerrado': ('#10b981', '#ecfdf5'),
    }
    fase_labels = {
        'disputa': 'Disputa',
        'pre_leilao': 'Pre-Leilao',
        'discovery': 'Descoberta',
        'encerrado': 'Encerrado',
    }

    cards = []
    for lote in LOTES:
        sid = str(lote['id'])
        est = state.get(sid, {})
        fase = est.get('fase', lote.get('fase', 'pre_leilao'))
        lance = est.get('lance_atual', 0) or lote.get('lance_inicial', 0)
        custo = est.get('custo', 0)
        if custo == 0:
            custo = calc_custo(lance, lote)
        margem_min = est.get('margem_min', 0)
        margem_max = est.get('margem_max', 0)
        score = est.get('score', 0)
        lance_ant = est.get('lance_anterior', 0) or lote.get('lance_inicial', 0)
        variacao = ((lance - lance_ant) / lance_ant * 100.0) if lance_ant > 0 else 0
        accent, bg = fase_colors.get(fase, ('#888', '#f5f5f5'))
        score_color = '#10b981' if score >= 7 else ('#f59e0b' if score >= 4 else '#ef4444')
        notas = _html_escape(lote.get('notas', '') or '')
        url = _html_escape(lote.get('url_lote', '#'))
        modelo = _html_escape(lote.get('modelo', ''))
        ano = _html_escape(lote.get('ano', ''))
        cor = _html_escape(lote.get('cor', ''))
        label_fase = fase_labels.get(fase, fase)
        margem_pct_val = est.get('margem_pct', 0)
        score_w = '%.0f' % (score * 10)
        score_str = '%.1f' % score
        variacao_str = '%+.1f' % variacao
        lance_str = format_currency(lance)
        custo_str = format_currency(custo)
        margem_min_str = format_currency(margem_min)
        margem_max_str = format_currency(margem_max)
        lote_id_str = str(lote['id'])
        disp_count = str(fases_count.get('disputa', 0))
        pre_count = str(fases_count.get('pre_leilao', 0))
        disc_count = str(fases_count.get('discovery', 0))
        enc_count = str(fases_count.get('encerrado', 0))

        card = '''<div class=card>
  <div class=card-header>
    <span class=card-id>LOTE ''' + lote_id_str + '''</span>
    <span class=card-fase style=background:''' + accent + ''';color:white>''' + label_fase + '''</span>
  </div>
  <div class=card-modelo>''' + modelo + ''' <span class=card-ano>''' + ano + '''</span></div>
  <div class=card-cor>''' + cor + '''</div>
  <div class=score-bar><div class=score-fill style=width:''' + score_w + '''%;background:''' + score_color + '''></div></div>
  <div class=score-label>score ''' + score_str + '''/10 &middot; margem ''' + ('%.0f' % margem_pct_val) + '''%</div>
  <div class=metrics>
    <div class=metric-row><span>Lance atual</span><span class=val style=color:''' + accent + '''>''' + lance_str + '''</span></div>
    <div class=metric-row><span>Custo total</span><span class=val>''' + custo_str + '''</span></div>
    <div class=metric-row><span>Margem</span><span class=val style=color:#10b981>''' + margem_min_str + ''' - ''' + margem_max_str + '''</span></div>
    <div class=metric-row><span>Variacao</span><span class=val>''' + variacao_str + '''%</span></div>
  </div>
  <div class=card-notas>''' + notas + '''</div>
  <a href=''' + url + ''' target=_blank class=card-btn>Ver lote &#8594;</a>
</div>'''
        cards.append(card)

    lotes_html = ''.join(cards)
    if not lotes_html:
        lotes_html = '<p style=color:#9ca3af;padding:20px;font-size:13pt>Nenhum lote monitorado.</p>'

    html = (
        '<!DOCTYPE html><html lang=pt-BR><head>'
        '<meta charset=UTF-8>'
        '<meta name=viewport content=width=device-width,initial-scale=1.0>'
        '<title>AlfaPrime Monitor</title>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Inter,-apple-system,sans-serif;background:#f8f9fc;color:#1a1a2e;min-height:100vh}'
        '.header{background:white;border-bottom:1px solid #e5e7eb;padding:24px 32px;display:flex;justify-content:space-between;align-items:center}'
        '.logo{font-size:20pt;font-weight:800;color:#1a1a2e}.logo span{color:#ff6b35}'
        '.header-right{text-align:right}.time{font-size:11pt;color:#6b7280}'
        '.status{font-size:10pt;color:#10b981;font-weight:600;margin-top:2px}'
        '.content{padding:28px 32px;max-width:1200px;margin:0 auto}'
        '.fases-bar{display:flex;gap:10px;margin-bottom:24px;flex-wrap:wrap}'
        '.fase-chip{padding:7px 14px;border-radius:20px;font-size:11pt;font-weight:600}'
        '.fase-disputa{background:#fff8f4;color:#ff6b35}'
        '.fase-pre_leilao{background:#eff6ff;color:#3b82f6}'
        '.fase-discovery{background:#f5f3ff;color:#8b5cf6}'
        '.fase-encerrado{background:#ecfdf5;color:#10b981}'
        '.section-title{font-size:12pt;font-weight:700;color:#9ca3af;margin-bottom:14px;text-transform:uppercase;letter-spacing:1px}'
        '.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}'
        '.card{background:white;border-radius:14px;padding:18px;border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05)}'
        '.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}'
        '.card-id{font-size:9pt;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1px}'
        '.card-fase{font-size:9pt;font-weight:700;padding:3px 9px;border-radius:10px}'
        '.card-modelo{font-size:14pt;font-weight:800;color:#1a1a2e}'
        '.card-ano{font-weight:400;color:#6b7280;font-size:12pt}'
        '.card-cor{font-size:10pt;color:#9ca3af;margin-top:2px}'
        '.score-bar{height:5px;background:#f3f4f6;border-radius:3px;margin:12px 0 4px;overflow:hidden}'
        '.score-fill{height:100%;border-radius:3px;transition:width .5s}'
        '.score-label{font-size:9pt;color:#9ca3af;margin-bottom:10px}'
        '.metrics{border-top:1px solid #f3f4f6;padding-top:10px}'
        '.metric-row{display:flex;justify-content:space-between;padding:4px 0;font-size:11pt}'
        '.metric-row span:first-child{color:#6b7280}'
        '.metric-row .val{font-weight:700;color:#1a1a2e}'
        '.card-notas{font-size:10pt;color:#9ca3af;margin-top:10px;line-height:1.4}'
        '.card-btn{display:block;text-align:center;margin-top:12px;padding:8px;background:#1a1a2e;color:white;border-radius:8px;text-decoration:none;font-size:10pt;font-weight:600}'
        '.card-btn:hover{background:#ff6b35}'
        '.footer{text-align:center;padding:20px;font-size:10pt;color:#9ca3af;border-top:1px solid #e5e7eb;margin-top:30px}'
        '</style></head>'
        '<body>'
        '<div class=header>'
        '<div class=logo>AlfaPrime<span>.</span></div>'
        '<div class=header-right>'
        '<div class=time>' + now_str + '</div>'
        '<div class=status>&#9679; Monitor ativo</div>'
        '</div></div>'
        '<div class=content>'
        '<div class=fases-bar>'
        '<div class=\"fase-chip fase-disputa\">Disputa (' + disp_count + ')</div>'
        '<div class=\"fase-chip fase-pre_leilao\">Pre-Leilao (' + pre_count + ')</div>'
        '<div class=\"fase-chip fase-discovery\">Descoberta (' + disc_count + ')</div>'
        '<div class=\"fase-chip fase-encerrado\">Encerrado (' + enc_count + ')</div>'
        '</div>'
        '<div class=section-title>Lotes monitorados</div>'
        '<div class=card-grid>' + lotes_html + '</div>'
        '</div>'
        '<div class=footer>AlfaPrime Transportes</div>'
        '</body></html>'
    )

    with open(BASE_DIR + '/dashboard/index.html', 'w') as f:
        f.write(html)
    log_msg('Dashboard atualizado.')

def run():
    now = datetime.now()
    log_msg('=' * 40)
    log_msg('INICIANDO - ' + now.strftime('%d/%m/%Y %H:%M'))
    state = load_state()
    history = load_history()
    alertas = []
    for lote in LOTES:
        lote_id = str(lote['id'])
        estado_anterior = state.get(lote_id, {}).copy()
        state, resultado = run_check_lote(lote, state)
        if resultado is None:
            continue
        estado_atual = state.get(lote_id, {})
        fase, info_fase = detectar_fase_do_estado(lote, estado_atual)
        estado_atual['fase'] = fase
        estado_atual['fase_info'] = info_fase
        lance = estado_atual.get('lance_atual', 0) or lote.get('lance_inicial', 0)
        custo, margem_min, margem_max, margem_pct, score = calc_margens(lote, lance)
        estado_atual['custo'] = round(custo, 2)
        estado_atual['margem_min'] = round(margem_min, 2)
        estado_atual['margem_max'] = round(margem_max, 2)
        estado_atual['margem_pct'] = round(margem_pct, 1)
        estado_atual['score'] = round(score, 1)
        estado_atual['fase_label'] = PHASE_CONFIG.get(fase, {}).get('label', fase)
        novos = checar_alertas(lote, estado_atual, estado_anterior)
        alertas.extend(novos)
        history.append({
            'timestamp': now.isoformat(),
            'lote_id': lote_id,
            'lance': estado_atual.get('lance_atual', 0),
            'fase': fase,
            'score': round(score, 1),
        })
        label = PHASE_CONFIG.get(fase, {}).get('label', fase)
        lance_fmt = format_currency(estado_atual.get('lance_atual', 0))
        log_msg('  ' + lote_id + ' | ' + str(lote.get('modelo')) + ' ' + str(lote.get('ano')) + ' | fase=' + label + ' | lance=' + lance_fmt + ' | score=' + ('%.1f' % score))
    save_state(state)
    save_history(history)
    if alertas:
        log_msg('ALERTAS: ' + str(len(alertas)))
        for a in alertas:
            log_msg('  ' + str(a.get('msg', '')))
        with open(DATA_DIR + '/alertas.json', 'w') as f:
            json.dump({'timestamp': now.isoformat(), 'alertas': alertas}, f, indent=2, default=str)
    gerar_dashboard(state)
    log_msg('OK - ' + str(len(LOTES)) + ' lotes verificados')
    return state, alertas

if __name__ == '__main__':
    run()