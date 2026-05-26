#!/usr/bin/env python3
from datetime import datetime, timedelta
from config import PHASE_CONFIG, LOTES

def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def detectar_fase(lote, estado_lote):
    hoje = datetime.now()
    data_fim = parse_date(lote.get('data_encerramento') or estado_lote.get('data_encerramento'))
    data_abertura = parse_date(lote.get('data_abertura') or lote.get('data_abertura'))
    status_site = str(estado_lote.get('status', '')).lower()
    tem_lance = estado_lote.get('lance_atual', 0) > 0

    if status_site in ('encerrado', 'vendido') or lote.get('fase') == 'encerrado':
        return 'encerrado', {}

    if tem_lance:
        if data_fim:
            horas = (data_fim - hoje).total_seconds() / 3600.0
            if horas > 0 and horas < 72:
                return 'disputa', {'horas_restantes': round(horas, 1)}
            elif horas > 0:
                return 'pre_leilao', {'horas_para_disputa': round((data_fim - hoje).total_seconds() / 3600.0, 1)}
        return 'pre_leilao', {'tem_lance': True}

    if data_fim:
        horas = (data_fim - hoje).total_seconds() / 3600.0
        if horas < 0:
            return 'encerrado', {}
        elif horas < 24:
            return 'disputa', {'horas_restantes': round(horas, 1)}
        else:
            return 'pre_leilao', {'dias_restantes': round(horas / 24.0, 1)}

    if data_abertura and hoje < data_abertura:
        dias = round((data_abertura - hoje).total_seconds() / 86400.0, 1)
        return 'discovery', {'dias_para_abertura': dias}

    return lote.get('fase', 'pre_leilao'), {}

def precisa_verificar(fase_atual, horas_desde_ultimo_check):
    if fase_atual == 'disputa':
        return horas_desde_ultimo_check >= 0.2
    elif fase_atual in ('discovery', 'pre_leilao'):
        return horas_desde_ultimo_check >= 20
    elif fase_atual == 'encerrado':
        return False
    return False

def gerar_cron_fases():
    crons = {}
    for fase, cfg in PHASE_CONFIG.items():
        if cfg.get('cron'):
            crons[fase] = cfg['cron']
    return crons

def montar_alerta_fase(fase, info):
    labels = {
        'discovery': 'Descoberta',
        'pre_leilao': 'Pre-Leilao',
        'disputa': 'Disputa',
        'encerrado': 'Encerrado',
    }
    label = labels.get(fase, fase)

    if fase == 'discovery':
        dias = info.get('dias_para_abertura', '?')
        return label + ' - Abre em ' + str(dias) + ' dia(s)'
    elif fase == 'pre_leilao':
        if info.get('horas_para_disputa'):
            dias = round(info.get('horas_para_disputa', 0) / 24.0, 0)
            return label + ' - Disputa em ~' + str(int(dias)) + ' dia(s)'
        if info.get('tem_lance'):
            return label + ' - Lances ja registrados'
        dias = info.get('dias_restantes', '?')
        return label + ' - Encerramento em ~' + str(dias) + ' dia(s)'
    elif fase == 'disputa':
        horas = info.get('horas_restantes', '?')
        return label + ' - Encerramento em ~' + str(horas) + 'h!'
    return label

if __name__ == '__main__':
    for lote in LOTES[:2]:
        estado = {'lance_atual': 0, 'status': '', 'data_encerramento': None}
        fase, info = detectar_fase(lote, estado)
        print(lote['id'] + ' (' + str(lote.get('modelo')) + '): ' + montar_alerta_fase(fase, info))