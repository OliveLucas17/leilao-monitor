#!/bin/bash
# Auto-start do dashboard de monitoramento
PORT=8880
DIR='/var/www/leilao-monitor'
PIDFILE='/tmp/leilao-dashboard.pid'

if [ -f $PIDFILE ]; then
    OLD_PID=$(cat $PIDFILE)
    if kill -0 $OLD_PID 2>/dev/null; then
        echo Dashboard ja em execucao PID=$OLD_PID
    else
        rm $PIDFILE
    fi
fi

cd $DIR
nohup python3 -m http.server $PORT &>/tmp/dash8880.log &
echo $! > $PIDFILE
echo Dashboard iniciado na porta $PORT