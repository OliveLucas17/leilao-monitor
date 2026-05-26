#!/usr/bin/env python3
import subprocess, re

def crawl_lote_ricoleiloes(lote):
    url = lote.get('url_lote') or ('https://www.ricoleiloes.com.br/lotes/veiculo?search=' + str(lote['id']))
    result = subprocess.run(
        ['gsk', 'crawl', url, '--render_js'],
        capture_output=True, text=True, timeout=120
    )
    text = result.stdout
    data = {
        'lance_atual': 0.0,
        'lance_inicial': lote.get('lance_inicial', 0),
        'status': 'desconhecido',
        'data_encerramento': None,
        'html_snippet': text[:2000],
        'erro': None,
    }
    if not text or len(text) < 100:
        data['erro'] = 'pagina vazia'
        return data

    if 'encerrado' in text.lower() or 'vendido' in text.lower():
        data['status'] = 'encerrado'
    elif 'aberto' in text.lower():
        data['status'] = 'aberto'

    m = re.search(r'R\\$\\s*([0-9]{1,3}(?:\\.[0-9]{3})*,[0-9]{2})', text)
    if m:
        try:
            val = float(m.group(1).replace('.', '').replace(',', '.'))
            if 100 < val < 1000000:
                data['lance_atual'] = val
        except:
            pass

    m = re.search(r'(?:Encerramento|Fechamento)[:\\s]*\\n?\\s*(\\d{1,2}[\\/\\s][A-Za-z]{3,9}[\\/\\s]\\d{2,4})', text, re.I)
    if m:
        data['data_encerramento'] = m.group(1).strip()

    if data['lance_atual'] == 0:
        data['lance_atual'] = lote.get('lance_inicial', 0)

    return data