#!/bin/bash

PID=$(ps -u luke -o pid,command | grep 'memcached'  | grep -v grep | cut -f1 -d ' ')

if [ "x$PID" == "x" ]
then
    memcached -d -m 24 -s ~/memcached.sock
fi

