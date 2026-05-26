#!/usr/bin/env python3
import subprocess, re

def crawl_lote_sumare(lote):
    url = lote['url_lote']
    result = subprocess.run(
        ['gsk', 'crawl', url, '--render_js'],
        capture_output=True, text=True, timeout=120
    )
    text = result.stdout
    data = {
        'lance_atual': 0.0,
        'lance_inicial': lote.get('lance_inicial', 0),
        'status': 'desconhecido',
        'data_encerramento': lote.get('data_encerramento'),
        'html_snippet': text[:2000],
        'erro': None,
    }
    if not text or len(text) < 100:
        data['erro'] = 'pagina vazia ou nao carregou'
        return data

    text_lower = text.lower()

    if 'encerrado' in text_lower or 'vendido' in text_lower:
        data['status'] = 'encerrado'
    elif 'aberto' in text_lower:
        if 'lance' in text_lower:
            data['status'] = 'lance_registrado'
        else:
            data['status'] = 'aberto_sem_lance'

    # Try multiple patterns
    patterns = [
        r'Lance Atual[:\\s]*([^\\n]{5,60})',
        r'R\\$\\s*([0-9]{1,3}(?:\\.[0-9]{3})*,[0-9]{2})',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            val_str = m.group(1)
            val_clean = re.sub(r'[^0-9.,]', '', val_str)
            try:
                val = float(val_clean.replace('.', '').replace(',', '.'))
                if val >= 100 and val < 1000000:
                    data['lance_atual'] = val
                    break
            except:
                pass

    if data['lance_atual'] == 0:
        data['lance_atual'] = lote.get('lance_inicial', 0)

    date_patterns = [
        r'Fechamento[:\\s]*\\n?\\s*([A-Z][a-z]{2,8}\\s+[0-9]{1,2}\\s+[A-Z][a-z]{2,8}\\s+[0-9]{2,4}\\s+[0-9]{1,2}:[0-9]{2})',
        r'Fechamento[:\\s]*\\n?\\s*(\\d{1,2}\\s+[A-Za-z]{3,9}\\s+\\d{2,4})',
        r'Encerramento[:\\s]*\\n?\\s*(\\d{1,2}/\\d{1,2}/\\d{2,4})',
    ]
    for p in date_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            data['data_encerramento'] = m.group(1).strip()
            break

    return data