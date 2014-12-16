#!/bin/sh

# create our roms directory:
mkdir ~/Documents/ROMs # might fail if directory exists, but that shouldn't be an issue
mkdir ~/Documents/ROMs/super\ nintendo\ entertainment\ system/
chown -R $SUDO_USER ~/Documents/ROMs

# put our emulators in place:
mkdir ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/
#  old emulator zip command: unzip -uqn Emulators\ v1.5.3.zip -d ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/
cp Game\ Launcher\ Emulator\ Pack.bundle/* ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/
chown -R $SUDO_USER ~/Library/Application\ Support/Plex\ Media\ Server/GameLauncher\ Emulators/

# put the plugin bundle in place:
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/
cp -R "Game Launcher.bundle" ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/
unzip -uqn ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/mamedb/mame.xml.zip
chown -R $SUDO_USER ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/


# configure our defaultprefs.json file for the current user:
sed -i '' "s/CURRENT_USERNAME/$SUDO_USER/g" ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Game\ Launcher.bundle/Contents/DefaultPrefs.json

# put the SDL framework in place:
cp -R SDL.framework /System/Library/Framework

# clear the old db:
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.gamelauncher.db

# clear the old prefs:
rm -rf ~/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Preferences/com.plexapp.plugins.gamelauncher.xml
