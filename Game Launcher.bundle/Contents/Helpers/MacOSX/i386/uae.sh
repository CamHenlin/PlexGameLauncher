#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

EMUPATH=${emupath}"UAE/"
TEMPDIR="WHDLoad/Temp/"
WHDuaerc="Configurations/A1200 Normal WHD.uaerc"
ADFuaerc="Configurations/A500 Normal.uaerc"

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

cd "$EMUPATH"

extension=${romname##*.}

if [ "$extension" == "zip" ]; then
	unzip "${romname}" -d $TEMPDIR
	find $TEMPDIR -maxdepth 1 -name *.info | while read dir
	do
       		filename=${dir##*/}
		name=${filename%.*}
		sed -i -e "s/\(echo \"Running.*$\)/echo \"Running $(echo ${name} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g').slave\";/g" WHDLoad/WHD/S/user-startup
		sed -i -e "s/\(cd dh1.*$\)/cd dh1:$(echo ${name} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g');/g" WHDLoad/WHD/S/user-startup
		sed -i -e "s/\(whdload .*$\)/whdload $(echo ${name} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g').slave PRELOAD;/g" WHDLoad/WHD/S/user-startup
	done

	open E-UAE.app --args -f "$EMUPATH$WHDuaerc"
	sleep 3
	while [ `ps -ef | grep E-UAE | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
		do sleep 1
	done

	rm -R $TEMPDIR/*
elif [ "$extension" == "adf" ]; then
	sed -i -e "s/\(floppy0=.*$\)/floppy0=$(echo ${romname} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g')/g" "${ADFuaerc}"

	open PUAE.app --args -f "$EMUPATH$ADFuaerc"
	sleep 3
	while [ `ps -ef | grep PUAE | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
		do sleep 1
	done

	sed -i -e "s/\(floppy0=\/.*$\)/floppy0=/g" "${ADFuaerc}"
else
	echo "Unsusported file format detected. Currently only ADF and WHDLOAD files are supported."
fi

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
