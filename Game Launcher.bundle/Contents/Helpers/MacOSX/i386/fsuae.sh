#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}
console=${args[2]}
multidisk=${args[3]}

IFS=';' read -ra multidiskArr <<< "${multidisk}"

EMUPATH=${emupath}"FS-UAE/"
TEMPDIR="WHDLoad/Temp/"
ConfigDir="Configurations/"
CDTVuaerc=$ConfigDir"cdtv.fs-uae"
CD32uaerc=$ConfigDir"cd32.fs-uae"
WHDuaerc=$ConfigDir"a1200 whd.fs-uae"
ADFuaerc=$ConfigDir"a500 adf.fs-uae"

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

cd "$EMUPATH"

extension=${romname##*.}
extension=$(echo ${extension} | tr '[:upper:]' '[:lower:]');

if [ "$extension" = "zip" ]; then

	unzip "${romname}" -d $TEMPDIR
	find $TEMPDIR -maxdepth 1 -name *.info | while read dir
	do
       	filename=${dir##*/}
		name=${filename%.*}
		sed -i -e "s/\(echo \"Running.*$\)/echo \"Running $(echo ${name} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g').slave\";/g" WHDLoad/WHD/S/user-startup
		sed -i -e "s/\(cd dh1.*$\)/cd dh1:$(echo ${name} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g');/g" WHDLoad/WHD/S/user-startup
		sed -i -e "s/\(whdload .*$\)/whdload $(echo ${name} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g').slave PRELOAD;/g" WHDLoad/WHD/S/user-startup
	done

	FS-UAE.app/Contents/MacOS/FS-UAE -c "$WHDuaerc"

	rm -R $TEMPDIR/*

elif [ "$extension" = "adf" ] && [ -n "$multidisk" ]; then

	OIFS=$IFS
	IFS='
'
	n=0
	for disk in ${multidiskArr[@]}; do
		sed -i -e "s/\(# floppy_drive_${n} =.*$\)/floppy_drive_${n} = $(echo ${disk} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g')/g" "${ADFuaerc}"
		((n++))
	done
	IFS=$OIFS

	FS-UAE.app/Contents/MacOS/FS-UAE -c "$ADFuaerc"

	OIFS=$IFS
	IFS='
'
	n=0
	for disk in ${multidiskArr[@]}; do
		sed -i -e "s/\(floppy_drive_${n} =.*$\)/# floppy_drive_${n} =/g" "${ADFuaerc}"
		((n++))
	done
	IFS=$OIFS
	echo "multi"

elif [ "$extension" = "adf" ]; then

	echo "not multi"
	sed -i -e "s/\(# floppy_drive_0 =.*$\)/floppy_drive_0 = $(echo ${romname} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g')/g" "${ADFuaerc}"
	FS-UAE.app/Contents/MacOS/FS-UAE -c "$ADFuaerc"
	sed -i -e "s/\(floppy_drive_0 =.*$\)/# floppy_drive_0 =/g" "${ADFuaerc}"

elif [ "$extension" = "cue" ]; then

	if [ "$console" = "commodore amiga cdtv" ]; then
		sed -i -e "s/\(# cdrom_drive_0 =.*$\)/cdrom_drive_0 = $(echo ${romname} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g')/g" "${CDTVuaerc}"
		FS-UAE.app/Contents/MacOS/FS-UAE -c "$CDTVuaerc"
		sed -i -e "s/\(cdrom_drive_0 =.*$\)/# cdrom_drive_0 =/g" "${CDTVuaerc}"
	else
		sed -i -e "s/\(# cdrom_drive_0 =.*$\)/cdrom_drive_0 = $(echo ${romname} | sed -e 's/\\/\\\\/g' -e 's/\//\\\//g' -e 's/&/\\\&/g')/g" "${CD32uaerc}"
		FS-UAE.app/Contents/MacOS/FS-UAE -c "$CD32uaerc"
		sed -i -e "s/\(cdrom_drive_0 =.*$\)/# cdrom_drive_0 =/g" "${CD32uaerc}"
	fi

else
	echo "Unsusported file format detected. Currently only ADF and WHDLOAD files are supported."
fi

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
