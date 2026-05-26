#!/usr/bin/env python3
import subprocess, os, json
from datetime import datetime

LOG = '/home/work/.openclaw/workspace/projects/leilao-monitor/data/monitor.log'
STATE = '/home/work/.openclaw/workspace/projects/leilao-monitor/data/state.json'
MONITOR = '/home/work/.openclaw/workspace/projects/leilao-monitor/monitor.py'

with open(LOG, 'a') as f:
    f.write(datetime.now().strftime('%Y-%m-%d %H:%M') + '\n')

state = {}
if os.path.exists(STATE):
    try:
        with open(STATE) as sf:
            state = json.load(sf)
    except:
        pass

disputa = sum(1 for v in state.values() if v.get('fase') == 'disputa')
today = datetime.now().strftime('%Y-%m-%d')
checks = [v.get('last_check', '') for v in state.values() if v.get('last_check')]
last_date = max(checks)[:10] if checks else ''

if disputa > 0:
    with open(LOG, 'a') as f:
        f.write('[run.sh] Modo rapido - ' + str(disputa) + ' disputa(s)\n')
    subprocess.run(['python3', MONITOR], stdout=open(LOG, 'a'), stderr=subprocess.STDOUT)
elif last_date != today:
    with open(LOG, 'a') as f:
        f.write('[run.sh] Daily check\n')
    subprocess.run(['python3', MONITOR], stdout=open(LOG, 'a'), stderr=subprocess.STDOUT)
else:
    with open(LOG, 'a') as f:
        f.write('[run.sh] Pulou - ja executado\n')