#!/bin/bash

args=("$@")
emulator=${args[0]}
codedir=${args[1]}

romname=${args[2]}
emupath=${args[3]}
console=${args[4]}
multidisk=${args[5]}
driver=${args[6]}



cd "${codedir}/Helpers"
./"${emulator}.sh" "${romname}" "${emupath}" "${console}" "${multidisk}" "${driver}" 1> ../Logs/emulator.out.log 2> ../Logs/emulator.err.log &

exit 0
