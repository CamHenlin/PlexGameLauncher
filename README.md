# Plex Game Launcher
---
### What the heck is this thing?

This is an emulator launcher frontend for Plex Media Center for numerous consoles (see Supported Consoles below)

### What is required?

- A Mac
- Plex Media Server on your Mac
- Plex Home Theater OR Plex Media Center the same Mac

Note! This will not run on any other products running Plex. Please don't try to get this running on your Roku, SmartTV (unless it's plugged into a Mac and not using the SmartTV functionality!), or any other products that run a Plex front end. It depends on being able to launch an emulator built for Mac OS 10.6 and better, which it certainly can't do on other platforms.

### How do I set it up?

####### Note to users of old game launcher: this will probably nuke your current game launcher instance and completely reset your configuration and will require you to reconfigure after installing or to move your ROMs to the new ROMs directory inside of your Documents folder.

To install, paste the following into your OS X terminal, press enter, and type in your password when prompted:

    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/CamHenlin/PlexGameLauncher/master/autoinstall.rb)"

There is a new ROMs directory inside of your Documents folder. There is a folder for every console, simply drop your ROMs in to those folders, restart Plex Media Server, reopen Plex Media Center, navigate to Videos, and open Game Launcher. Once in game launcher, and before playing any games, you will need to navigated to the maintenance section and have the Game Launcher search for ROMs, which may take several minutes. After that, you're ready to go!

### Having trouble?
##### We want to know about it!

Please [file a ticket](https://github.com/CamHenlin/PlexGameLauncher/issues) or look at existing tickets!

Note that we provide assistance getting PlexGameLauncher to import your games from the standard location, and getting it to launch emulators properly. Configuring the emulators to use your controllers, troubleshooting games, or helping you get this working on your SmartTV is not something we have time for.

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