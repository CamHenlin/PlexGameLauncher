# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin
# by Aequitas

import os,io
from subprocess import call
import xml.etree.ElementTree as et

#********** Get Pref *********
''' This will get a value from a Pref setting in the settings file '''
@route(PREFIX + '/getPref')
def getPref(key):
	Log.Debug('getPref called for key: %s' %(key))
	myFile = os.path.join(Core.app_support_path, 'Plug-ins', TITLE + '.bundle', 'http', 'jscript', 'settings.js')
	with io.open(myFile) as fin:
		for line in fin:
			if 'var ' + key + ' =' in line:
				drop, value = line.split('= "')
				value = value[:-3]
	return value

# Store a pref setting
''' Allows webpart to store a setting in settings.js '''
@route(PREFIX + '/SetPref')
def SetPref(Secret, Pref, Value):
	if PwdOK(Secret):
		Log.Debug('Got a call to set %s to %s in settings.js' %(Pref, Value))
		Value = Value.replace("\\", "/")
		Log.Debug('Value is now %s' %(Value))
		try:
			bDone = False
			myFile = os.path.join(Core.app_support_path, 'Plug-ins', TITLE + '.bundle', 'http', 'jscript', 'settings.js')
			with io.open(myFile) as fin, io.open(myFile + '.tmp', 'w') as fout:
				for line in fin:
					if 'var ' + Pref + ' = ' in line:
						line = 'var ' + Pref + ' = "' + Value + '";\n'
						bDone = True
					fout.write(unicode(line))
			if bDone == False:
				with io.open(myFile + '.tmp', 'a') as fout:
					line = 'var ' + Pref + ' = "' + Value + '";\n'
					fout.write(unicode(line))
			os.rename(myFile, myFile + '.org')
			os.rename(myFile + '.tmp', myFile)
			return 'ok'
		except:
			return 'error'
	else:
		return ERRORAUTH

#********** Validate Prefs *********
@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
	if setPMSPath():
		Log.Debug('Prefs are valid, so lets update the js file')
		myFile = os.path.join(Core.app_support_path, 'Plug-ins', TITLE + '.bundle', 'http', 'jscript', 'settings.js')
		global MYSECRET
		MYSECRET = Hash.MD5(Dict['secret'] + Prefs['PMS_Path'])
		with io.open(myFile) as fin, io.open(myFile + '.tmp', 'w') as fout:
			for line in fin:
				if 'var Secret =' in line:
					line = 'var Secret = "' + MYSECRET + '";\n'
				elif 'var PMSUrl =' in line:
					line = 'var PMSUrl = "' + Prefs['PMS_Path'] + '";\n'
				fout.write(unicode(line))
		os.rename(myFile, myFile + '.org')
		os.rename(myFile + '.tmp', myFile)
	return

#********** Set Secret *********
''' This will save a unique GUID in the dict, that is used as a seed for the secret '''
@route(PREFIX + '/setSecretGUID')
def setSecretGUID():
	Dict['secret'] = String.UUID()
	Dict.Save()
	return

#********** Create Website *********
''' Create symbolic links in the WebClient, so we can access this bundle frontend via a browser directly '''
@route(PREFIX + '/setup')
def setupSymbLink():
	src = Core.storage.join_path(Core.app_support_path, 'Plug-ins', TITLE + '.bundle', 'http')
	dst = Core.storage.join_path(Core.app_support_path, 'Plug-ins', 'WebClient.bundle', 'Contents', 'Resources', 'GameLauncher')
	if not os.path.lexists(dst):
		if Platform.OS=='Windows':
			Log.Debug('Darn ' + Platform.OS)
			# Cant create a symb link on Windows, until Plex moves to Python 3.3
			#call(["C:\Users\TM\AppData\Local\Plex Media Server\Plug-ins\WebTools.bundle\RightClick_Me_And_Select_Run_As_Administrator.cmd"])
			return False
		else:
		# This creates a symbolic link for the bundle in the WebClient.
		# URL is http://<IP of PMS>:32400/web/WebTools/index.html
			os.symlink(src, dst)
			Log.Debug("SymbLink not there, so creating %s pointing towards %s" %(dst, src))
			return True
	else:
		Log.Debug("SymbLink already present")
		return True

#********** Check secret *********
''' Check if the Secret provided is valid
Returns true is okay, and else false '''
@route(PREFIX + '/PwdOK')
def PwdOK(Secret):
	if (Hash.MD5(Dict['secret'] + Prefs['PMS_Path']) == Secret):
		return True
	elif Secret == Dict['secret']:
		return True
	else:
		return False

#********** Set PMS path *********
@route(PREFIX + '/setPMSPath')
def setPMSPath():
	Log.Debug('Entering setPMSPath')
	# Let's check if the PMS path is valid
	myPath = Prefs['PMS_Path']
	Log.Debug('My master set the Export path to: %s' %(myPath))
	try:
		#Let's see if we can add out subdirectory below this
		tmpTest = XML.ElementFromURL('http://' + myPath + ':32400')
		return True
	except:
		Log.Critical('Bad pmsPath')
		return False
