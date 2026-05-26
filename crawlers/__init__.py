# crawlers/__init__.py
from .sumare import crawl_lote_sumare
from .ricoleiloes import crawl_lote_ricoleiloes
from .hastasp import crawl_lote_hastasp

CRAWLERS = {
    'sumare': crawl_lote_sumare,
    'ricoleiloes': crawl_lote_ricoleiloes,
    'hastasp': crawl_lote_hastasp,
}

def crawl(lote):
    '''Dispara o crawler correto baseado no site do lote'''
    site = lote.get('site', 'sumare')
    fn = CRAWLERS.get(site)
    if not fn:
        raise ValueError(f'Crawler desconhecido: {site}')
    return fn(lote)