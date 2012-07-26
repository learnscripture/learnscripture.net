#! /bin/bash

export PATH=/usr/kerberos/bin:/usr/local/bin:/bin:/usr/bin:/home/cciw/bin:/home/cciw/.local/bin:/home/cciw/bin:/home/cciw/.local/bin:/home/cciw/.cabal/bin

NAME=supervisord
SUPERVISORD=/home/cciw/webapps/learnscripture_django/venv/bin/supervisord
SUPERVISORCTL=/home/cciw/webapps/learnscripture_django/venv/bin/supervisorctl
PIDFILE=/home/cciw/webapps/learnscripture_django/venv/etc/supervisord.pid
PS=$NAME
TRUE=1
FALSE=0

test -x $SUPERVISORD || exit 0

isRunning(){
    pidof_daemon
    PID=$?

    if [ $PID -gt 0 ]; then
    return 1
    else
        return 0
    fi
}

pidof_daemon() {
    PIDS=`pidof -x $PS` || true

    [ -e $PIDFILE ] && PIDS2=`cat $PIDFILE`

    for i in $PIDS; do
        if [ "$i" = "$PIDS2" ]; then
            return 1
        fi
    done
    return 0
}

start () {
    echo "Starting Supervisor daemon manager..."
    isRunning
    isAlive=$?

    if [ "${isAlive}" -eq $TRUE ]; then
        echo "Supervisor is already running."
    else
        $SUPERVISORD $OPTS || echo "Failed...!"
        echo "OK"
    fi
}

stop () {
    echo "Stopping Supervisor daemon manager..."
    $SUPERVISORCTL shutdown ||  echo "Failed...!"
    echo "OK"
}

case "$1" in
  start)
    start
    ;;

  stop)
    stop
    ;;

  restart|reload|force-reload)
    stop
    start
    ;;

esac

exit 0
