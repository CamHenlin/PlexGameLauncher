#!/bin/bash
SCRIPT_DIR=$(dirname $0)

# create our roms directory:
mkdir ~/Documents/ROMs # might fail if directory exists, but that shouldn't be an issue:
mkdir ~/Documents/ROMs/mame/
mkdir ~/Documents/ROMs/aae/
mkdir ~/Documents/ROMs/daphne/
mkdir ~/Documents/ROMs/sega\ naomi/
mkdir ~/Documents/ROMs/sammy\ atomiswave/
mkdir ~/Documents/ROMs/capcom\ play\ system/
mkdir ~/Documents/ROMs/sega\ model\ 2/
mkdir ~/Documents/ROMs/sega\ model\ 3/
mkdir ~/Documents/ROMs/cave\ sh3/
mkdir ~/Documents/ROMs/toaplan/
mkdir ~/Documents/ROMs/zinc/
mkdir ~/Documents/ROMs/atari\ 2600/
mkdir ~/Documents/ROMs/atari\ 5200/
mkdir ~/Documents/ROMs/atari\ 7800/
mkdir ~/Documents/ROMs/coleco\ colecovision/
mkdir ~/Documents/ROMs/nec\ pc-fx/
mkdir ~/Documents/ROMs/nec\ turbografx-16/
mkdir ~/Documents/ROMs/nec\ turbografx-cd/
mkdir ~/Documents/ROMs/nec\ supergrafx/
mkdir ~/Documents/ROMs/nintendo\ 64/
mkdir ~/Documents/ROMs/nintendo\ entertainment\ system/
mkdir ~/Documents/ROMs/nintendo\ gamecube/
mkdir ~/Documents/ROMs/nintendo\ wii/
mkdir ~/Documents/ROMs/nintendo\ wii\ virtual\ console/
mkdir ~/Documents/ROMs/sega\ 32x/
mkdir ~/Documents/ROMs/sega\ cd/
mkdir ~/Documents/ROMs/sega\ dreamcast/
mkdir ~/Documents/ROMs/sega\ genesis/
mkdir ~/Documents/ROMs/sega\ master\ system/
mkdir ~/Documents/ROMs/sega\ saturn/
mkdir ~/Documents/ROMs/sega\ sg-1000/
mkdir ~/Documents/ROMs/sony\ playstation/
mkdir ~/Documents/ROMs/sony\ playstation\ 2/
mkdir ~/Documents/ROMs/super\ nintendo\ entertainment\ system/
mkdir ~/Documents/ROMs/atari\ lynx/
mkdir ~/Documents/ROMs/bandai\ wonderswan/
mkdir ~/Documents/ROMs/bandai\ wonderswan\ color/
mkdir ~/Documents/ROMs/nintendo\ ds/
mkdir ~/Documents/ROMs/nintendo\ game\ boy/
mkdir ~/Documents/ROMs/nintendo\ game\ boy\ color/
mkdir ~/Documents/ROMs/nintendo\ game\ boy\ advance/
mkdir ~/Documents/ROMs/sega\ game\ gear/
mkdir ~/Documents/ROMs/sony\ playstation\ portable/
mkdir ~/Documents/ROMs/atari\ 8-bit/
mkdir ~/Documents/ROMs/commodore\ 64/
mkdir ~/Documents/ROMs/commodore\ amiga/
mkdir ~/Documents/ROMs/commodore\ amiga\ cd32/
mkdir ~/Documents/ROMs/commodore\ amiga\ cdtv/
mkdir ~/Documents/ROMs/msx-2/
mkdir ~/Documents/ROMs/mac\ os/
mkdir ~/Documents/ROMs/residualvm/
mkdir ~/Documents/ROMs/scummvm/
mkdir ~/Documents/ROMs/sinclair\ zx\ spectrum/

chown -R $SUDO_USER ~/Documents/ROMs

# put our emulators in place:
mkdir ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/
mkdir ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/Emulators/
# don't forget that we need to have the emulator zip in place:
unzip -uqn $SCRIPT_DIR/Emulators\ v1.5.3.zip -d ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/
cp -R $SCRIPT_DIR/Emulators/* ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/Emulators/
chown -R $SUDO_USER ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/

# put the plugin bundle in place:
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/
cp -R $SCRIPT_DIR/"Game Launcher.bundle" ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/
unzip -uqn ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/mamedb/mame.xml.zip
chown -R $SUDO_USER ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/


# configure our defaultprefs.json file for the current user:
sed -i '' "s/CURRENT_USERNAME/$SUDO_USER/g" ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/Contents/DefaultPrefs.json

# put the SDL framework in place:
cp -R $SCRIPT_DIR/SDL.framework /System/Library/Framework

# clear the old db:
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.gamelauncher.db

# clear the old prefs:
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Preferences/com.plexapp.plugins.gamelauncher.xml
