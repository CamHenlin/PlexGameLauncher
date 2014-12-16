#!/bin/bash

args=("$@")
codedir=${args[0]}
serverport=${args[1]}
sqlitepath=${args[2]}

cd "${codedir}/Code"
./webserver.py -- "${serverport}" "${sqlitepath}" 1> ../Logs/webserver.out.log 2> ../Logs/webserver.err.log &
#./webserver.py -- "${serverport}" "${sqlitepath}"
exit 0
