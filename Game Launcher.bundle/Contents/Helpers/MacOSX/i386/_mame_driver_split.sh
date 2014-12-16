#!/bin/bash

args=("$@")
emupath=${args[0]}

emu="${emupath}"/MAME/mame64plain
mamesystems="${emupath}"/MAME/mamesystems.csv
#mamelist="${emupath}"/MAME/mamelist.csv
#temp="${emupath}"/MAME/tempmame.csv

# See http://en.wikipedia.org/wiki/Arcade_system_board for a list of manufacturers and system boards

# this will grep all roms for a specific driver, example: neogeo, naomi 
${emu} -lb neogeo | awk '{ print $2","$3 }' | sed -E '/^neogeo/d' | sed -E 's/,neogeo//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Neo Geo MVS/' > ${mamesystems} # Neo geo MVS
${emu} -lb sams64 | awk '{ print $2","$3 }' | sed -E '/^hng64/d' | sed -E 's/,hng64//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Hyper Neo Geo 64/' >> ${mamesystems} # Hyper Neo Geo 64

${emu} -lb cpzn1 | awk '{ print $2","$3 }' | sed -E '/^cpzn1|^cpzn2|^tps|^taitofx1|^acpsx|^atpsx|^vspsx|^atluspsx|^psarc95/d' | \
	sed -E 's/,cpzn1|,cpzn2|,tps|,taitofx1|,acpsx|,atpsx|,vspsx|,atluspsx|,psarc95//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sony ZN board/' >> ${mamesystems} # Sony ZN-1 & ZN-2

${emu} -lb atarisy1 | awk '{ print $2","$3 }'  | sed -E '/^atarisy1/d'  | sed -E 's/,atarisy1//' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Atari System 1/' >> ${mamesystems} # Atari System 1
${emu} -lb paperboy | awk '{ print $2","$3 }'  | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Atari System 2/' >> ${mamesystems} # Atari System 2

${emu} -lb nbajam | awk '{ print $2","$3 }'  | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Midway T Unit/' >> ${mamesystems} # Midway T Unit

# Vector based games also run by the emulator AAE
${emu} -lb zektor | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega G80/' >> ${mamesystems} # Sega G80
${emu} -lb starwars | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Vector/' >> ${mamesystems} # starwars.c
${emu} -lb wotw | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Vector/' >> ${mamesystems} # cinemat.c
${emu} -lb tempest | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Vector/' >> ${mamesystems} # tempest.c
${emu} -lb wow | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Vector/' >> ${mamesystems} # astrocde.c

# Namco	
${emu} -lb amidar | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco Galaxian/' >> ${mamesystems} # Namco Galaxian
${emu} -lb tekken | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System 11/' >> ${mamesystems} # Namco system 11
${emu} -lb shadowld | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System 1/' >> ${mamesystems} # Namco system 1
${emu} -lb finallap | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System 2/' >> ${mamesystems} # Namco system 2
${emu} -lb winrun | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System 21/' >> ${mamesystems} # Namco system 21
${emu} -lb emeralda | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System NA-1/' >> ${mamesystems} # Namco system NA1
${emu} -lb ptblank | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System NB-1/' >> ${mamesystems} # Namco system NB1
${emu} -lb acedrvrw | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System 22/' >> ${mamesystems} # Namco system 22
${emu} -lb mrdrillr | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System 12/' >> ${mamesystems} # Namco system 12
${emu} -lb panicprk | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco System 23/' >> ${mamesystems} # Namco system 23

${emu} -lb snowbro2 | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Namco/' >> ${mamesystems} # Taoplan

${emu} -lb 1941 | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Capcom Play System 1/' >> ${mamesystems} # Capcom Play System 1 cps1.c
${emu} -lb 1944 | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Capcom Play System 2/' >> ${mamesystems} # Capcom Play System 2 cps2.c
${emu} -lb sfiii | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Capcom Play System 3/' >> ${mamesystems} # Capcom Play System 3 cps3.c

#Konami
${emu} -lb salamand | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Konami/' >> ${mamesystems} # Konami nemesis.c
${emu} -lb bm1stmix | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Konami/' >> ${mamesystems} # Konami djmain.c
${emu} -lb salmndr2 | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Konami GX/' >> ${mamesystems} # Konami GX
${emu} -lb polystar | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Konami M2/' >> ${mamesystems} # Konami M2

#Sega
${emu} -lb choplift | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega System 1/' >> ${mamesystems} # Sega System 1
${emu} -lb shinobi | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega System 16/' >> ${mamesystems} # Sega System 16
${emu} -lb bnzabros | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega System 24/' >> ${mamesystems} # Sega System 24
${emu} -lb orunners | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega System 32/' >> ${mamesystems} # Sega System 32
${emu} -lb vf | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega Model 1/' >> ${mamesystems} # Sega Model 1
${emu} -lb daytona | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega Model 2/' >> ${mamesystems} # Sega Model 2
${emu} -lb bass | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega Model 3/' >> ${mamesystems} # Sega Model 3
${emu} -lb naomi | awk '{ print $2","$3 }' | sed -E '/^naomi/d' | sed -E 's/(naomi.*)//g' | sed -E 's/,$//' | sed -E '/awbios/d'  | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega Naomi/' >> ${mamesystems} # Sega Naomi
${emu} -lb braveff | awk '{ print $2","$3 }' | sed -E '/^hikaru/d' | sed -E 's/,hikaru//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega Hikaru/' >> ${mamesystems} # Sega Hikaru
${emu} -lb outr2 | awk '{ print $2","$3 }' | sed -E '/^chihiro/d' | sed -E 's/,chihiro//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Sega Chihiro/' >> ${mamesystems} # Sega Chihiro

${emu} -lb 18wheelr  | awk '{ print $2","$3 }' | sed -E '/awbios/!d'  | sed -E '/^awbios/d' | cut -d ',' -f1 | sed -E 's/(.+)/\1,Sammy Atomiswave/' >> ${mamesystems} # Sammy Atomiswave

# Taito
${emu} -lb waterski | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Taito SJ/' >> ${mamesystems} # Taito SJ
${emu} -lb gigandes | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Taito X/' >> ${mamesystems} # Taito X
${emu} -lb spacegun | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Taito Z/' >> ${mamesystems} # Taito Z
${emu} -lb viofight | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Taito B/' >> ${mamesystems} # Taito B
${emu} -lb kurikint | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Taito L/' >> ${mamesystems} # Taito L
${emu} -lb tcobra2 | awk '{ print $2","$3 }' | sed -E 's/,$//' | sed -E '/,/d' | sed -E 's/(.+)/\1,Taito F3/' >> ${mamesystems} # Taito F3

# strip the incorrect line endings from the romlister output
#sed 's/.$//' ${mamelist} > ${temp}
# match the fist colum from mamesystems.csv file to the first column of mamelist.csv 
# append the contents from mamesystems.csv to mamelist.csv
#awk 'NR==FNR{A[$1]=$2;next}$0{$9=A[$1];print}'  FS=, OFS=, "${mamesystems}" "${temp}" > "${emupath}/MAME/mamecombined.csv"
# clean up our mess
#rm ${temp}
#rm ${mamesystems}


