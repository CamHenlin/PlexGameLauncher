# Plex Game Launcher
---
### What the heck is this thing?

This is an emulator launcher frontend for Plex Media Center for numerous consoles (see Supported Consoles below)

### What is required?

- A Mac
- Plex Media Server
- Plex Home Theater OR Plex Media Center

### How do I set it up?

####### Note to users of old game launcher: this will probably nuke your current game launcher instance and completely reset your configuration and will require you to reconfigure after installing or to move your ROMs to the new ROMs directory inside of your Documents folder.

#### Youtube install video: [link](https://www.youtube.com/watch?v=8XPwH-__Y3I&spfreload=10)

Download [gamelauncher.zip](https://github.com/CamHenlin/PlexGameLauncher/raw/master/gamelauncher.zip)

Download [Emulators v1.5.3.zip](http://dl.dropbox.com/u/9111377/Emulators%20v1.5.3.zip)

Unzip gamelauncher.zip

Place an *unzipped* copy of the Emulators directory (not the contents of the directory, the directory itself!) from the Emulators v1.5.3.zip inside the unzipped copy of gamelauncher.zip (Note: I realize this is obnoxious, but the emulators pack is too large for github. I will attempt to better sort this out in future releases.)

Open Terminal.app, type 'sudo ' (note the space), and drag install.sh from the unzipped gamelauncher into the terminal. You will be prompted for your password. Enter it, and in a few moments, Game Launcher will be installed. Note: You must do this as the user you will be running plex as. It will not function for other users on the computer.

There is a new ROMs directory inside of your Documents folder. There is a folder for every console, simply drop your ROMs in to those folders, restart Plex Media Server, reopen Plex Media Center, navigated to Videos, and open Game Launcher. Once in game launcher, and before playing any games, you will need to navigated to the maintenance section and have the Game Launcher search for ROMs, which may take several minutes. After that, you're ready to go!

After doing all this, you will still need to configure your specific emulators manually.

### Having trouble?
##### We want to know about it!

Please [file a ticket](https://github.com/CamHenlin/PlexGameLauncher/issues) or look at existing tickets!

### Supported Consoles:
- Atari 2600
- Atari 7800
- Atari Lynx
- Bandai Wonderswan
- Bandai Wonderswan Color
- Cave SH3
- Coleco Colecovision
- Commodore 64
- Commodore Amiga
- Commodore Amiga CD32
- Commodore Amiga CDTV
- Daphne
- Mac OS ( genuine mac games / steam shortcuts )
- MAME
- MSX-2
- Nec SuperGrafx
- Nec TurboGrafx-16
- Nintendo 64
- Nintendo Entertainment System
- Nintendo Game Boy
- Nintendo Game Boy Advance
- Nintendo Game Boy Color
- Nintendo GameCube
- Nintendo Wii
- Nintendo Wii Virtual Console
- ResidualVM
- ScummVM
- Sega 32X
- Sega CD
- Sega Dreamcast
- Sega Game Gear
- Sega Genesis
- Sega Master System
- Sega Model 3
- Sega SG-1000
- Sinclair ZX Spectrum
- Sony Playstation
- Sony Playstation 2
- Super Nintendo Entertainment System