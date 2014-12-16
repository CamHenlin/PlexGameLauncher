#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}



open -a "$emupath"BSNES/BSNES (Accuracy).app "$romname"


