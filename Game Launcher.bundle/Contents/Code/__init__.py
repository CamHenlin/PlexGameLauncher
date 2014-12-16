# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin revised
# by Aequitas

# Original Plex Game Launcher Plugin
# by Nudgenudge <nudgenudge@gmail.com>

import os,sys,subprocess,re,sqlite3,unicodedata,csv,time,datetime
import zlib,zipfile
import textwrap
import md5
from dateutil import parser
from htmlentitydefs import name2codepoint
from Queue import Queue
from threading import Thread

# import all grabbers
import mameworld
import progettoemma
import giantbomb
import gamefaqs
import archive
import thegamesdb
import allgame
import mobygames

PREFIX = '/video/gamelauncher'
TITLE = 'Game Launcher'

IMG_THUMB = 'icon-default.png'
IMG_ART = 'art-default.jpg'
PREFS_ICON = 'icon-prefs.png'

EMU_ROOT = ""
ROM_ROOT = ""
ARCHIVE	= [".zip"]

PMS_DIR = Core.app_support_path
CODE_DIR = Core.storage.join_path(PMS_DIR, 'Plug-ins', TITLE + '.bundle', 'Contents')
SQL_DIR = Core.storage.join_path(PMS_DIR, 'Plug-in Support', 'Databases')

# dummy Select to create the DB if not created yet
SQDB = sqlite3.connect(SQL_DIR + '/com.plexapp.plugins.gamelauncher.db', check_same_thread = False, detect_types=sqlite3.PARSE_DECLTYPES)
SQDB.text_factory = lambda x: unicode(x, "utf-8", "ignore")
Database = SQDB.cursor

# dummy Select to create the DB if not created yet
SQDBopenvg = ''
SQDBmame = ''

POOL = None

#import webserver setup script
import webserver

####################################################################################################
class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = False
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try: func(*args, **kargs)
            except Exception, e: print e
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

    def queue_size(self):
        """Check if queue is empty"""
    	self.tasks.qsize()

####################################################################################################
def Start():
	Log("Starting Game Launcher")

	Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")
	Plugin.AddViewGroup("InfoList", viewMode = "InfoList", mediaType = "items")
	Plugin.AddViewGroup("MediaPreview", viewMode = "MediaPreview", mediaType = "items")
	Plugin.AddViewGroup("Showcase", viewMode = "Showcase", mediaType = "items")
	Plugin.AddViewGroup("Pictures", viewMode = "Pictures", mediaType = "items")
	Plugin.AddViewGroup("PanelStream", viewMode = "PanelStream", mediaType = "items")
	Plugin.AddViewGroup("WallStream", viewMode = "WallStream", mediaType = "items")

	global SQDB, Database, POOL

	# dummy Select to create the DB if not created yet
	#SQDB = sqlite3.connect(SQL_DIR + '/com.plexapp.plugins.gamelauncher.db', check_same_thread = False, detect_types=sqlite3.PARSE_DECLTYPES)
	#SQDB.text_factory = lambda x: unicode(x, "utf-8", "ignore")
	#Database = SQDB.cursor

	#test to see if this is the first time we start it, initialize db
	CheckTables()

	# Load the needed config files
	LoadConfigFiles()

	# Start the threadpool for the grabber with 100 workers
	POOL = ThreadPool(100)

	ObjectContainer.view_group = 'InfoList'
	ObjectContainer.title1 = TITLE
	ObjectContainer.art = R(IMG_ART)
	DirectoryObject.thumb = R(IMG_THUMB)
	DirectoryObject.art = R(IMG_ART)

	OpenVGDB_Check()

	# Setup webserver
	webserver.setupSymbLink()
	webserver.setSecretGUID()
	webserver.SetPref(Dict['secret'], 'PathToPlexMediaFolder', Core.app_support_path.replace("\\", "/"))
	webserver.ValidatePrefs()

####################################################################################################
def LoadConfigFiles():
	global SYSTEMS_LIST, EMULATORS, DAPHNE
	SYSTEMS_LIST = JSON.ObjectFromString( Resource.Load('json/systems.json') )
	EMULATORS = JSON.ObjectFromString( Resource.Load('json/emulators.json') )
	DAPHNE = JSON.ObjectFromString( Resource.Load('json/daphne.json') )

####################################################################################################
def ValidatePrefs():
	EMU_ROOT = Prefs['EMU_ROOT']
	ROM_ROOT = Prefs['ROM_ROOT']
	webserver.SetPref(Dict['secret'], 'PMSUrl', Prefs['PMS_Path'])

	if not EMU_ROOT:
		return MessageContainer( L('MSG_TITLE_ERROR'), L('MSG_BODY_EMUROOT'))
	elif not ROM_ROOT:
		return MessageContainer( L('MSG_TITLE_ERROR'), L('MSG_BODY_ROMROOT'))
	else:
		return MessageContainer( L('MSG_TITLE_SUCCESS'), L('MSG_BODY_SETTINGSSAVED'))

####################################################################################################
def OpenVGDB_Check():
	# Check for openvgdb
	LastCheck = Dict['OpenVGDB_Check']
	LastVersion = Dict['OpenVGDB_Ver']

	d = datetime.timedelta(days=14)

	if (LastCheck == None):
		LastCheck = datetime.datetime.now() - d

	checking = datetime.datetime.now()
	checked = LastCheck

	Log('DEBUG: Seeing if we need to check for OpenVGDB update ...')

	# Only check once every 2 weeks
	if (checking > checked + d):
		Log('DEBUG: Starting check for new OpenVGDB version')

		github = JSON.ObjectFromURL("https://api.github.com/repos/OpenVGDB/OpenVGDB/releases?page=1&per_page=1")
		version = github[0]['tag_name']
		published = parser.parse(github[0]['published_at']).replace(tzinfo=None)
		downloadfile = github[0]['assets'][0]['browser_download_url']

		if (published > checked):
			Log('DEBUG: Grabbing OpenVGDB Update!')
			import urllib
			downloaded = urllib.urlretrieve(downloadfile, "openvgdb.zip")
			archiveFile = zipfile.ZipFile(downloaded[0], 'r')
			contents = archiveFile.infolist()
			extractdir = archiveFile.extract('openvgdb.sqlite', CODE_DIR + '/OpenVGDB')
			Log('DEBUG: OpenVGDB Updated!')
			Dict['OpenVGDB_Ver'] = version
		else:
			Log('DEBUG: No OpenVGDB update available')

	Dict['OpenVGDB_Check'] = checking
	Dict.Save()

	return True

####################################################################################################
def OpenVGDBScan(crc, fileTitle, console):

	global SQDBopenvg
	SQDBopenvg = sqlite3.connect(CODE_DIR + '/OpenVGDB/openvgdb.sqlite', check_same_thread = False, detect_types=sqlite3.PARSE_DECLTYPES)
	SQDBopenvg.text_factory = lambda x: unicode(x, "utf-8", "ignore")
	OpenVGDB = SQDBopenvg.cursor

	Log('DEBUG: OpenVGDB: Searching for: ' + fileTitle)

	grabber = {}

	if crc == None:
		sql = "SELECT DISTINCT releaseTitleName as 'title' \
		, 	releaseDescription as 'description' \
		,	releaseDeveloper as 'developer' \
		,	releasePublisher as 'publisher' \
		,	releaseDate as 'year' \
		,	releaseGenre as 'genre' \
		, 	releaseCoverFront as 'url_boxart' \
		FROM	ROMs \
				JOIN RELEASES Release USING (romID) \
				JOIN SYSTEMS System USING (systemID) \
		WHERE	romExtensionlessFileName LIKE ? \
		AND		systemName LIKE ?;"

		for game in SQDBopenvg.execute(sql, ['%'+fileTitle+'%', console]):
			grabber['scanned'] = 1
			grabber['title'] = game[0]
			grabber['description'] = game[1]
			grabber['developer'] = game[2]
			grabber['publisher'] = game[3]
			try:
				grabber['year'] = re.search('\d{4}', str(game[4])).group(0)
			except:
				grabber['year'] = None
			grabber['genre'] = game[5]
			grabber['url_boxart'] = game[6]
			Log('DEBUG: Found file title in OpenVGDB and taking it!')

	else:
		sql = "SELECT DISTINCT releaseTitleName as 'title' \
		, 	releaseDescription as 'description' \
		,	releaseDeveloper as 'developer' \
		,	releasePublisher as 'publisher' \
		,	releaseDate as 'year' \
		,	releaseGenre as 'genre' \
		, 	releaseCoverFront as 'url_boxart' \
		FROM ROMs rom \
		INNER JOIN SYSTEMS system USING (systemID) \
		LEFT JOIN RELEASES release USING (romID) \
		WHERE 	romHashCRC = ?;"

		for game in SQDBopenvg.execute(sql, [crc]):
			grabber['scanned'] = 1
			grabber['title'] = game[0]
			grabber['description'] = game[1]
			grabber['developer'] = game[2]
			grabber['publisher'] = game[3]
			try:
				grabber['year'] = re.search('\d{4}', str(game[4])).group(0)
			except:
				grabber['year'] = None
			grabber['genre'] = game[5]
			grabber['url_boxart'] = game[6]
			Log('DEBUG: Found CRC Hash for title in OpenVGDB and taking it!')

		# If we did not match on CRC, try again on file title
		if len(grabber) == 0:
			Log('DEBUG: OpenVGDB: Did not find CRC hash, trying again with title for: ' + fileTitle)
			grabber = OpenVGDBScan(None, fileTitle, console)

	return grabber

####################################################################################################
def MameDBScan(rom):

	global SQDBmame
	SQDBmame = sqlite3.connect(CODE_DIR + '/OpenVGDB/mamedb.sqlite', check_same_thread = False, detect_types=sqlite3.PARSE_DECLTYPES)
	SQDBmame.text_factory = lambda x: unicode(x, "utf-8", "ignore")
	MameDB = SQDBmame.cursor

	sql = "SELECT DISTINCT name as 'title' \
	, 	description as 'description' \
	,	manufacturer as 'publisher' \
	,	year as 'year' \
	,	genre as 'genre' \
	FROM 	Mame \
	WHERE 	filename_rom = ?;"

	grabber = {}
	for game in SQDBmame.execute(sql, [rom]):
		grabber['scanned'] = 1
		grabber['title'] = game[0]
		grabber['description'] = game[1]
		grabber['publisher'] = game[2]
		try:
			grabber['year'] = re.search('\d{4}', str(game[3])).group(0)
		except:
			grabber['year'] = None
		grabber['genre'] = game[4]
		grabber['url_screen'] = "http://www.progettoemma.net/snap/%s/0000.png" % (rom)

		Log('DEBUG: Found CRC Hash for title in MameDB and taking it!')
	return grabber

####################################################################################################
@handler(PREFIX, TITLE, thumb=IMG_THUMB, art=IMG_ART)
@route(PREFIX + '/MainMenu')
def MainMenu(Func='', Secret='', **kwargs):
	if Func=='':
		system = list()
		for systems in SYSTEMS_LIST['systems']:
			system.append(systems)
		system.sort()

		oc = ObjectContainer()

		if (Prefs['ENABLE_FAVORITES']):
			oc.add(DirectoryObject(key = Callback(GetAllGamesList, title = L("MENU_FAVORITES"), cat = "favorites"), title = L("MENU_FAVORITES")))
		oc.add(DirectoryObject(key = Callback(GetAllGamesList, title = L("MENU_ALL_GAMES")), title = L("MENU_ALL_GAMES")))
		oc.add(DirectoryObject(key = Callback(StartRandomGame, title = L("MENU_RANDOM_GAME")), title = L("MENU_RANDOM_GAME")))

		if (Prefs['SEPERATE_ARCADE_LIST']):
			for sys in system:
				if (SystemCheck(sys)):
					oc.add(DirectoryObject(key = Callback(GetSystemList, title = sys.capitalize(), system = sys), title = sys.capitalize()))
		else:
			oc.add(DirectoryObject(key = Callback(GetConsoleList, title = L("MENU_CONSOLE")), title = L("MENU_CONSOLE")))
		oc.add(DirectoryObject(key = Callback(SearchList, title = L("MENU_SEARCH")), title = L("MENU_SEARCH")))
		oc.add(DirectoryObject(key = Callback(MaintenanceList, title = L("MENU_MAINTENANCE")), title = L("MENU_MAINTENANCE"), thumb = R(PREFS_ICON)))
		return oc
	elif Func=='allconsoles':
		return GetXMLFileFromUrl(Secret, kwargs.get("Url").split('&_')[0])

####################################################################################################
def SystemCheck(sys):
	str = ""
	for system in SYSTEMS_LIST['systems'][sys]:
		str += " OR lower(console) == '" + system + "'"

	for console in SQDB.execute("SELECT DISTINCT console FROM games WHERE " + str[3:] + ";"):
		return True
	return False

####################################################################################################
@route(PREFIX + '/searchlist')
def SearchList(title):
	oc = ObjectContainer(title2 = title)

	oc.add(InputDirectoryObject(key = Callback(SearchForRom, title = L("MENU_SEARCH_ROM")), title = L("MENU_SEARCH_ROM"), prompt = 'Search Game / Publisher'))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_GENRE"), query = "genre"), title = L("MENU_GENRE")))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_YEAR"), query = "year"), title = L("MENU_YEAR")))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_PUBLISHER"), query = "publisher"), title = L("MENU_PUBLISHER")))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_DEVELOPER"), query = "developer"), title = L("MENU_DEVELOPER")))

	#if (Prefs['MAMEDB_LIST']):
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_SEARCH_NRPLAYERS"), query = "players"), title = L("MENU_SEARCH_NRPLAYERS")))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_SEARCH_NRBUTTONS"), query = "buttons"), title = L("MENU_SEARCH_NRBUTTONS")))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_SEARCH_CONTROLLER"), query = "controller"), title = L("MENU_SEARCH_CONTROLLER")))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_SEARCH_ORIENTATION"), query = "orientation"), title = L("MENU_SEARCH_ORIENTATION")))
	oc.add(DirectoryObject(key = Callback(SearchAll, title = L("MENU_SEARCH_SYSTEM"), query = "board"), title = L("MENU_SEARCH_SYSTEM")))

	return oc

####################################################################################################
@route(PREFIX + '/maintenancelist')
def MaintenanceList(title):
	oc = ObjectContainer(title2 = title)
	oc.add(DirectoryObject(key = Callback(RefreshDB), title = L("MENU_PREF_REFRESH_ROM")))
	oc.add(DirectoryObject(key = Callback(ListUnknown, title = L("MENU_PREF_LIST_UNKOWN")), title = L("MENU_PREF_LIST_UNKOWN")))
	oc.add(DirectoryObject(key = Callback(GetMissingInfo, query="unknown"), title = L("MENU_PREF_REFRESH_UNKNOWN")))
	oc.add(DirectoryObject(key = Callback(GetMissingInfo), title = L("MENU_PREF_REFRESH_INFO")))
	oc.add(DirectoryObject(key = Callback(ListSystemInfo, title = L("MENU_PREF_DELETE_SYSTEM")), title = L("MENU_PREF_DELETE_SYSTEM")))

	#if (Prefs['MAMEDB_LIST']):
		#oc.add(DirectoryObject(key = Callback(ImportMameList), title = L("MENU_PREF_REFRESH_MAME")))
		#oc.add(DirectoryObject(key = Callback(ImportMameSystems), title = L("MENU_PREF_GENERATE_SYSTEMS")))

	oc.add(PrefsObject(title = L('MENU_PREFERENCES'), thumb = R(PREFS_ICON)))
	return oc

####################################################################################################
@route(PREFIX + '/listunknown')
def ListUnknown(title):
	oc = ObjectContainer(title2 = title)
	for game in SQDB.execute("SELECT console, title FROM games WHERE scanned = '0' AND (filename_disknr is Null or filename_disknr = 1) ORDER BY console;"):
		oc.add(DirectoryObject(key = Callback(doNothing), title=game[0] +" - "+ game[1]))
	return oc

####################################################################################################
def ListSystemInfo(title):
	oc = ObjectContainer(title2 = title)
	for console in SQDB.execute("SELECT DISTINCT console FROM games ORDER BY console;"):
		oc.add(DirectoryObject(key = Callback(DelSystemInfo, console = console[0]), title="Delete info for: "+console[0]))
	return oc

####################################################################################################
@route(PREFIX + '/delsysteminfo')
def DelSystemInfo(console):
	result = SQDB.execute("SELECT filename FROM games WHERE console = ?;", [console] )
	count = result.fetchall()
	if (len(count) > 0):
		result = SQDB.execute("DELETE FROM games WHERE console = ?;", [console] )
		return MessageContainer(L("MSG_TITLE_SUCCESS"), console+" is removed")
	else:
		return MessageContainer(L("MSG_TITLE_ERROR"), "Data for "+console+" is not present")

####################################################################################################
@route(PREFIX + '/delrominfo')
def DelRomInfo(id):
	result = SQDB.execute("SELECT rom_id FROM games WHERE rom_id = ?;", [id] )
	count = result.fetchall()
	if (len(count) > 0):
		result = SQDB.execute("DELETE FROM games WHERE rom_id = ?;", [id] )
		return MessageContainer(L("MSG_TITLE_SUCCESS"), id+" is removed")
	else:
		return MessageContainer(L("MSG_TITLE_ERROR"), "Data for id "+id+" is not present")

####################################################################################################
@route(PREFIX + '/saverom')
def SaveRom(json):
	new = JSON.ObjectFromString(json)
	sqlupdate = 'UPDATE games SET title = ?, description = ?, url_boxart = ? WHERE rom_id = ?;'
	values = [new['title'].decode('utf-8'), new['description'].decode('utf-8'), new['url_boxart'].decode('utf-8'), new['id']]
	SQDB.execute(sqlupdate, values)
	SQDB.commit()
	Log(new)
	return True

####################################################################################################
#	A dirty hack to assure all tables are created. DefaultSql file allows only 1 statement, a second throws up an error
####################################################################################################
def CheckTables():

	try:
		result = SQDB.execute("SELECT * FROM mame LIMIT 1")
	except SQDB.Error, e:
		try:
			result = SQDB.execute("CREATE TABLE games (rom_id INTEGER PRIMARY KEY, filename TEXT, filename_archive TEXT, filename_crc TEXT, filename_rom TEXT, filename_disknr INTEGER, scanned INTEGER, console TEXT, title TEXT, description BLOB, publisher TEXT, developer TEXT, year INTEGER, genre TEXT, players INTEGER, url_trailer TEXT, url_boxart TEXT, url_fanart TEXT, url_screen TEXT, url_banner TEXT, favorite INTEGER, region TEXT, CONSTRAINT unique_game UNIQUE (filename, filename_archive, console));")
			SQDB.commit()
		except SQDB.Error, e:
			Log("Well there is something wrong with your SQL! %s " % e)
		try:
			result = SQDB.execute("CREATE INDEX IF NOT EXISTS index_filename_rom_games ON games (filename_rom);")
			SQDB.commit()
		except SQDB.Error, e:
			Log("Well there is something else wrong with your SQL!")


####################################################################################################
def ImportMameList():

	try:
		result = SQDB.execute("DELETE FROM mame;")
		SQDB.commit()
	except SQDB.Error, e:
		Log("Sqlite error! Sqlite responded: " + e.args[0])

	try:
		gameList = csv.reader(open(os.path.join(Prefs['EMU_ROOT'], 'MAME/mamelist.csv'), 'rb'), delimiter=',', quotechar='|')
	except:
		return MessageContainer(L("MSG_TITLE_ERROR"), L("DB_REFRESH_MAME_FAILED"))

	for row in gameList:
		if ((row[5] == "90") or (row[5] == "270")):
			row[5] = "1"	#vertical orientation
		else:
			row[5] = "0"	#horizontal orientation
		row[6] = row[6].split("/")[0]
		try:
			row[8]
		except:
			row.append("")
		SQDB.execute("INSERT INTO mame VALUES (?,?,?,?,?,?,?,?,?);", row)
	SQDB.commit()
	return MessageContainer(L("MSG_TITLE_SUCCESS"), L("DB_REFRESH_MAME"))

####################################################################################################
def ImportMameSystems():
	Log(Helper.Run("_mame_driver_split.sh", os.path.join(Prefs['EMU_ROOT'], 'Emulators/')))

	result = SQDB.execute("SELECT * FROM mame;")
	count = result.fetchall()
	if (len(count) > 0):
		try:
			gameSystems = csv.reader(open(os.path.join(Prefs['EMU_ROOT'], 'MAME/mamesystems.csv'), 'rb'), delimiter=',', quotechar='|')
			for row in gameSystems:
				SQDB.execute("UPDATE mame SET board = (?) WHERE filename_rom = ?;", (row[1], row[0]) )
			SQDB.commit()
		except:
			return MessageContainer(L("MSG_TITLE_ERROR"), L("DB_MAMESYSTEMS_FAILED"))

		return MessageContainer(L("MSG_TITLE_SUCCESS"), L("DB_GENERATE_MAME"))
	else:
		return MessageContainer(L("MSG_TITLE_ERROR"), L("DB_MAMELIST_EMPTY"))

####################################################################################################
def RefreshDB():
	Log("REFRESH DB")
	# Reload the needed config files
	LoadConfigFiles()

	CleanUpRoms()

	if (not os.path.isdir(Prefs['ROM_ROOT'])):
		return MessageContainer(L("MSG_TITLE_ERROR"), L("Roms dir "+Prefs['ROM_ROOT']+" does not exist."))

	FillRoms()
	return MessageContainer(L("MSG_TITLE_SUCCESS"), L("DB_REFRESH_ROMS"))

####################################################################################################
def FillRoms():
	Log("FILL ROMS")
	global POOL

	tempGameList = SQDB.execute("SELECT filename, console FROM games;")
	gameList = []
	for game in tempGameList:
		gameList.append(game)

#	if (Prefs['MAMEDB_LIST']):
	sql = ""
	if (Prefs['MAMEDB_SHOW_CLONES'] != True):
		sql = sql + " WHERE cloneof is null"
	if (Prefs['MAMEDB_SHOW_MATURE'] != True):
		if sql == "":
			sql = sql + " WHERE mature is null"
		else:
			sql = sql + " AND mature is null"

	if (Prefs['MAMEDB_SHOW_STATUS'] == 'Playable & Imperfect'):
		if sql == "":
			sql = sql + " WHERE status in ('good','imperfect')"
		else:
			sql = sql + " AND status in ('good','imperfect')"
	elif (Prefs['MAMEDB_SHOW_STATUS'] == 'Playable'):
		if sql == "":
			sql = sql + " WHERE status = 'good'"
		else:
			sql = sql + " AND status = 'good'"

	sql = "SELECT filename_rom FROM mame" + sql

	global SQDBmame
	SQDBmame = sqlite3.connect(CODE_DIR + '/OpenVGDB/mamedb.sqlite', check_same_thread = False, detect_types=sqlite3.PARSE_DECLTYPES)
	SQDBmame.text_factory = lambda x: unicode(x, "utf-8", "ignore")

	tempMameList = SQDBmame.execute(sql)
	mameList = []
	for game in tempMameList:
		mameList.append(game[0].lower())
	# else:
	# 	mameList = None

	basedir = os.path.join(Prefs['ROM_ROOT'], '')
	for console in os.listdir(basedir):
		if (os.path.isdir(os.path.join(basedir,console))):
			SearchRoms(os.path.join(basedir, console), gameList, mameList, console)

	# Wait until all threads are finished
	POOL.wait_completion()
	SQDB.commit()
	Log('DEBUG: Done scanning!')

####################################################################################################
def GetArchiveContents(filename):
	files = {}
	extension = os.path.splitext(filename)[1].lower()
	if (extension == '.zip'):
		zip = zipfile.ZipFile(filename, 'r')
		contents = zip.infolist()
		zip.close()
		for rom in contents:
			# skip dotfiles and resource files
			if (os.path.basename(rom.filename)[:1] == "." or os.path.basename(rom.filename)[:1] == "_" or rom.filename[:1] == "." or rom.filename[:1] == "_"):
				continue

			files[rom.filename] = "%X"%(rom.CRC & 0xFFFFFFFF)
		return files

####################################################################################################
#	Recursive search for roms, exclude unwanted dirs
####################################################################################################
def SearchRoms(dir, gameList, mameList, console):
	global POOL

	basedir = dir
  	Log("Searching for roms in: %s" % dir)
	subdirlist = []
	for game in os.listdir(dir):
		Log("Game %s" % game)

		fileFullLocation = os.path.join( os.path.join(Prefs['ROM_ROOT'], console ), os.path.join(basedir,game) )
		fileRelLocation = re.sub(os.path.join(Prefs['ROM_ROOT'], console + os.path.sep), '', os.path.join(basedir,game))
		fileName = os.path.splitext(game)[0]
		fileExtension = os.path.splitext(game)[1].lower()

		# Hack to allow for native mac application to be scanned
		if (os.path.splitext(game)[1].lower() == ".app"):
			if ( (fileRelLocation,console) not in gameList ):
				Log("DEBUG: Found MacOSX application adding: " + fileName)

				if (Prefs['THREADED_GRABBER']):
					POOL.add_task(FetchData, console, fileFullLocation, fileRelLocation, fileName, None, None)
				else:
					FetchData(console, fileFullLocation, fileRelLocation, fileName, None, None)

			continue

		if os.path.isfile(os.path.join(basedir, game)):
			Log("Game %s is a file" % game)
			if ( (fileRelLocation,console) not in gameList ):
				Log("Game %s not in game list" % game)

				if ( fileExtension in ARCHIVE and ( console.lower() not in SYSTEMS_LIST['systems']['arcade'] ) ):
					Log("Game %s is an archive" % game)
					# We found an archive file, get the contents of the zipfile to see if we can find a file that we support
					resultScan = False
					archiveContents = GetArchiveContents(fileFullLocation)
					for fileNameArchive, fileCRC in archiveContents.iteritems():
						fileName = os.path.splitext(fileNameArchive)[0]
						fileExtension = os.path.splitext(fileNameArchive)[1].lower()

						if ( os.path.splitext(fileNameArchive)[1].lower() in GetExtensionForEmulators(console.lower()) ):
							Log('Found rom inside archive: ' + game + ' that we support: ' + fileNameArchive)
							resultScan = True

							if (Prefs['THREADED_GRABBER']):
								POOL.add_task(FetchData, console, fileFullLocation, fileRelLocation, fileName, fileNameArchive, fileCRC)
							else:
								FetchData(console, fileFullLocation, fileRelLocation, fileName, fileNameArchive, fileCRC)

					fileName = os.path.splitext(game)[0]
					fileExtension = os.path.splitext(game)[1].lower()

					if ( (not resultScan) and ( fileExtension in GetExtensionForEmulators(console.lower() ) ) ):
						# Woops, we scanned the archive but didn't find anything we could use, add it anyway since the emulator supports archive files natively
						# Mainly done for Amiga WHDLoad, there are no supported files in there
						if (Prefs['THREADED_GRABBER']):
							POOL.add_task(FetchData, console, fileFullLocation, fileRelLocation, fileName, None, None )
						else:
							FetchData(console, fileFullLocation, fileRelLocation, fileName, None, None)

				else:
					if ( fileExtension in GetExtensionForEmulators(console.lower()) and ( console.lower() not in SYSTEMS_LIST['systems']['arcade']) ):
						Log("Game %s file ext matches console" % game)
						# Work around for the sandbox ( because we are pulling the file in memory, limit filesize )
						file_size = os.path.getsize(fileFullLocation)
						fileCRC = None
						if ( file_size < 100000000 ):
							file_contents = Core.storage.load(fileFullLocation)
							fileCRC = "%X"%(zlib.crc32(file_contents) & 0xFFFFFFFF)
							file_contents = None

						if ( fileCRC == "0" ):
							fileCRC = None

						# Dirty hack for residualvm and scummvm, we use the directory name as the game name since the lnk file we match is used as the gameid to fire the emulator
						if (console.lower() == "residualvm" or console.lower() == "scummvm"):
							fileName = os.path.split(basedir)[1]

						if (Prefs['THREADED_GRABBER']):
							POOL.add_task(FetchData, console, fileFullLocation, fileRelLocation, fileName, None, fileCRC )
						else:
							FetchData(console, fileFullLocation, fileRelLocation, fileName, None, fileCRC)


					else:
						Log("Game %s probably arcade" % game)
						if ( fileExtension in GetExtensionForEmulators(console.lower()) ):
							# if console is mame and we choose to only include only games that are on the working list, do an additional check
							if ((console == "MAME") and ((fileName.lower()) not in mameList)):
								Log("SKIPPING rom: " + game + " since it not on the working list")
								continue

							# Dirty hack for daphne, since it uses framefiles with alternate names, we manually try to match them
							if (console.lower() == "daphne" and fileName in DAPHNE):
								fileName = DAPHNE[fileName]
							elif (console.lower() == "daphne" and fileName not in DAPHNE):
								continue

							if (Prefs['THREADED_GRABBER']):
								POOL.add_task(FetchData, console, fileFullLocation, fileRelLocation, fileName, None, None)
							else:
								FetchData(console, fileFullLocation, fileRelLocation, fileName, None, None)

							Log("EDIT: Adding Game "+game+" for system: "+console)

        	else:
				Log("Game %s in gamelist" % game)
				if (game.lower() not in Prefs['EXCLUDE_DIRS'].lower().split(",")):
					subdirlist.append(os.path.join(basedir, game))
				#else:
				#	Log("Skipping dir: " + os.path.join(basedir, game))

	for subdir in subdirlist:
		SearchRoms(subdir, gameList, mameList, console)

####################################################################################################
def FetchData(console, fileFullLocation, fileRelLocation, fileName, fileNameArchive, fileCRC):

	# Check for disc information
	gameCDinfo = GetDiskInfo(fileRelLocation)

	gameParams = {}
	Log('Fetching data for ROM ' + fileName)

	if (gameCDinfo != None):
		if (gameCDinfo['number'] == 1):
			gameParams = FetchDataForId(fileCRC, fileName, console)
			gameParams['filename_rom'] = stripReleaseInfo(fileName)
			gameParams['filename_disknr'] = gameCDinfo['number']
		else:
			gameParams = {}
			gameParams['scanned'] = 0
			gameParams['filename_rom'] = stripReleaseInfo(fileName)
			gameParams['filename_disknr'] = gameCDinfo['number']
			Log("EDIT: Adding rom without scanning since its part of a larger multi disk set")
	else:
		gameParams = FetchDataForId(fileCRC, fileName, console)

	# We hack the romname so when scan for new roms and thing on the mamelist change, we are able to detect it.
	if ( console.lower() in SYSTEMS_LIST['systems']['arcade'] and (console.lower() != "daphne") ):
		gameParams['filename_rom'] = fileName

	if ( fileNameArchive ):
		gameParams['filename_archive'] = fileNameArchive
	if ( fileCRC ):
		gameParams['filename_crc'] = fileCRC


	gameParams['filename'] = fileRelLocation	# set the full relative location of the romfile
	if (gameParams['scanned'] == 0):
		gameParams['title'] = fileName.split('[')[0].split('(')[0].rstrip()
	gameParams['favorite'] = 0					# set the default value for favorites
	gameParams['console'] = console				# set the console

	fields = gameParams.keys()
	values = gameParams.values()
	fieldlist = ",".join(fields)
	placeholderlist = ",".join(["?"] * len(fields))
	query = "insert into games (%s) values (%s);" % (fieldlist, placeholderlist)
	SQDB.execute(query, values)
	# SQDB.commit()
	return True

####################################################################################################
#		Determin if we have a multidisk set
####################################################################################################
def GetDiskInfo(rom):
	info = {}
	#gameCD = re.search('(\(cd ?[0-9]{1}(\)?|[ ]{1}[a-zA-Z0-9].+?)\)|\(disc ?[0-9]{1}(\)?|[ ]{1}[a-zA-Z0-9].+?)\)|\(disk ?[0-9]{1}(\)?|[ ]{1}[a-zA-Z0-9].+?)\))', rom, re.I)
	gameCD = re.search('(\(cd ?[0-9]{1}(\)?|[ ]{1}[a-zA-Z0-9].+?)\)|\[cd ?[0-9]{1}(\]?|[ ]{1}[a-zA-Z0-9].+?)\]|\(dis[ck] ?[0-9]{1}(\)?|[ ]{1}[a-zA-Z0-9].+?)\)|\[dis[ck] ?[0-9]{1}(\]?|[ ]{1}[a-zA-Z0-9].+?)\])', rom, re.I)
	if (gameCD):
		if (re.search('(cd)', rom, re.I)):
			info['text'] = "CD"
		if (re.search('(disc)', rom, re.I)):
			info['text'] = "Disc"
		if (re.search('(disk)', rom, re.I)):
			info['text'] = "Disk"

		gameCDnumber = re.search('([0-9]{1})', gameCD.group(1), re.I)
		info['number'] = int(gameCDnumber.group(1))

		return info
	else:
		return None

####################################################################################################
#		Get the list of known extensions for each emulator combined by system
####################################################################################################
def GetExtensionForEmulators(console):
	extensions = list()
	for systemtype in SYSTEMS_LIST['systems']:
		for system in SYSTEMS_LIST['systems'][systemtype]:
			if (console == system):
				for emulator in SYSTEMS_LIST['systems'][systemtype][system]:
					for extension in EMULATORS[emulator]:
						if (extension not in extensions):
							extensions.append(extension)
	return extensions

####################################################################################################
#		Run all the grabbers we can get to retrieve game info
####################################################################################################
def FetchDataForId(fileCRC, fileTitle, console, gameParams=None, rerun=None, fuzzy=None):

	if (gameParams == None):
		gameParams = {}

	if ( console.lower() in SYSTEMS_LIST['systems']['arcade'] and (console.lower() != "daphne") ):
		if (fileTitle and rerun == None):
			gameParams = MameDBScan(fileTitle)

		# for mameorder in ( Prefs['MAME_GRABBER_ORDER'].lower().split("->") ):
		# 	fuzzy = True
		# 	if (mameorder == 'progettoemma'):
		# 		if ( not checkMissingInfo(gameParams, progettoemma.Capabilities) ):
		# 			try:
		# 				gameParams = progettoemma.search(fileTitle, console, gameParams)
		# 			except:
		# 			 	Log("ERROR: We encountered an unrecoverable error from progettoemma: skipping for title")
	else:

		if (Prefs['USE_OPENVGDB'] and rerun == None):
			gameParams = OpenVGDBScan(fileCRC, fileTitle, console)

		for order in ( Prefs['CONSOLE_GRABBER_ORDER'].lower().split("->") ):
			if (order == 'giantbomb'):
				if ( not checkMissingInfo(gameParams, giantbomb.Capabilities) ):
					try:
						gameParams = giantbomb.search(fileTitle, console, gameParams, fileCRC, fuzzy)
					except:
						Log("ERROR: We encountered an unrecoverable error from giantbomb: skipping for title")
			if (order == 'gamefaqs'):
				if ( not checkMissingInfo(gameParams, gamefaqs.Capabilities) ):
					try:
						gameParams = gamefaqs.search(fileTitle, console, gameParams, fileCRC, fuzzy)
					except:
					 	Log("ERROR: We encountered an unrecoverable error from gamefaqs: skipping for title")
			if (order == 'mobygames'):
				if ( not checkMissingInfo(gameParams, mobygames.Capabilities) ):
					try:
						gameParams = mobygames.search(fileTitle, console, gameParams, fileCRC, fuzzy)
					except:
					 	Log("ERROR: We encountered an unrecoverable error from mobygames: skipping for title")
			if (order == 'archive'):
				if ( not checkMissingInfo(gameParams, archive.Capabilities) ):
					try:
						gameParams = archive.search(fileTitle, console, gameParams, fileCRC, fuzzy)
					except:
						Log("ERROR: We encountered an unrecoverable error from archive.vg: skipping for title")
			if (order == 'thegamesdb'):
				if ( not checkMissingInfo(gameParams, thegamesdb.Capabilities) ):
					try:
						gameParams = thegamesdb.search(fileTitle, console, gameParams, fileCRC, fuzzy)
					except:
						Log("ERROR: We encountered an unrecoverable error from thegamesdb: skipping for title")
			if (order == 'allgame'):
				if ( not checkMissingInfo(gameParams, allgame.Capabilities) ):
					try:
						gameParams = allgame.search(fileTitle, console, gameParams, fileCRC, fuzzy)
					except:
						Log("ERROR: We encountered an unrecoverable error from allgame: skipping for title")

			# Log(order)
			# Log(gameParams)

			if('url_boxart' in gameParams):
				if gameParams['url_boxart'] != None:
					excludedomain = re.findall('image.com.com', gameParams['url_boxart'] )
					if(excludedomain):
						del(gameParams['url_boxart'])


	if (len(gameParams) == 0 or rerun == None):
		# Do a quick test to see if we don't find any matches because we are searching for a game with a number that is not in roman format
		decimalNumbers = re.findall(' ([0-9]{1,2})', fileTitle.split('[')[0].split('(')[0].rstrip() )
		if (decimalNumbers and rerun == None):
			decimalDens=[1000,900,500,400,100,90,50,40,10,9,5,4,1]
			romanDens=["M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"]
			romanNotation = decToRoman( int(decimalNumbers[0]), "", decimalDens, romanDens )
			fileTitle = fileTitle.replace(decimalNumbers[0], romanNotation)
			Log("DEBUG: Found number in filename, retrying with roman notation")
			gameParams = FetchDataForId(fileCRC, fileTitle, console, gameParams, True)

		# If we still got nothing, then add it without data
		if ( (len(gameParams) == 0) and (fuzzy == None) and (int(Prefs['MATCH_PERCENT']) > 0) and (int(Prefs['MATCH_PERCENT']) < 100) ):
			Log("DEBUG: We did not find anything on our previous search, retrying but this time with fuzzy matching enabled")
			gameParams = FetchDataForId(fileCRC, fileTitle, console, gameParams, True, int(Prefs['MATCH_PERCENT']) )

		# If we still got nothing, then add it without data
		if (len(gameParams) == 0):
			gameParams['scanned'] = 0

	# Sanitize the data we got
	if (Prefs['SANITIZE_GENRE']):
		if ('genre' in gameParams):
			gameParams['genre'] = sanitizeGenre(gameParams['genre'])
	if ('publisher' in gameParams):
		gameParams['publisher'] = sanitizePubl(gameParams['publisher'])
	if ('description' in gameParams):
		gameParams['description'] = sanitizeDescr(gameParams['description'])

	return gameParams

####################################################################################################
#		Do a basic check to see if we recieved all the information we need
####################################################################################################
def checkMissingInfo(gameParams, grabberCapabilities):
	if (gameParams != None):

		# if we don't want fanart, remove it from the capabilities so we don't search for it
		if (Prefs['SCRAPE_FANART'] == False):
			if ('url_fanart' in grabberCapabilities):
				grabberCapabilities.remove('url_fanart') # fanart

		# these have no use yet in the interface, so remove them by default. They are still picked up when found
		if ('url_banner' in grabberCapabilities):
			grabberCapabilities.remove('url_banner') # bannerart
		if ('url_trailer' in grabberCapabilities):
			grabberCapabilities.remove('url_trailer') # bannerart

		for key in grabberCapabilities:
			if (key in gameParams):
				if (gameParams[key] == None):
					# We are missing data for the title we are scanning
					return False
				if (gameParams[key] == ""):
					return False
			else:
				# We are missing data for the title we are scanning
				return False
		return True
	return False

####################################################################################################
#		Check our current DB for roms with missing info
####################################################################################################
@route(PREFIX + '/getmissinginfo')
def GetMissingInfo(query=None):

	if (query == "unknown"):
		sql = "SELECT * FROM games WHERE scanned = 0 AND (filename_disknr is Null or filename_disknr = 1);"
	else:
		if (Prefs['SCRAPE_FANART']):
			sql = "SELECT * FROM games WHERE (url_boxart is Null OR description is Null OR publisher is Null OR developer is Null OR year is Null OR genre is Null OR url_fanart is Null) AND scanned = 1 AND (filename_disknr is Null or filename_disknr = 1);"
		else:
			sql = "SELECT * FROM games WHERE (url_boxart is Null OR description is Null OR publisher is Null OR developer is Null OR year is Null OR genre is Null) AND scanned = 1 AND (filename_disknr is Null or filename_disknr = 1);"

	for game in SQDB.execute(sql):
		fileFullLocation = os.path.join(Prefs['ROM_ROOT'], game[7], game[1])

		if (game[1] == None):
			fileName = os.path.basename(game[1])
		else:
			fileName = os.path.basename(game[2])
		fileTitle = os.path.splitext(fileName)[1]

		# Dirty hack for daphne, since it uses framefiles with alternate names, we manually try to match them
		if (game[7].lower() == "daphne" and fileTitle in DAPHNE):
			fileTitle = DAPHNE[fileTitle]
		elif (game[7].lower() == "daphne" and fileTitle not in DAPHNE):
			continue

		# Dirty hack for residualvm and scummvm, we use the directory name as the game name since the lnk file we match is used as the gameid to fire the emulator
		if (game[7].lower() == "residualvm" or game[8].lower() == "scummvm"):
			fileTitle = os.path.split(os.path.split(game[1])[0])[-1]

		#if (game[0] != "Roms/Super Mario World 2 - Yoshi's Island (USA) (Rev 1).zip"):
		#	continue

		Log("EDIT: Refreshing game info for: "+fileTitle+" for console: "+game[7])

		if (query == None):
			currentdata = {}
			currentdata['title'] = game[8]
			if (game[8] != None):
				currentdata['description'] = game[9]
			if (game[9] != None):
				currentdata['publisher'] = game[10]
			if (game[10] != None):
				currentdata['developer'] = game[11]
			if (game[11] != None):
				currentdata['year'] = game[12]
			if (game[12] != None):
				currentdata['genre'] = game[13]
			if (game[13] != None):
				currentdata['players'] = game[14]
			if (game[14] != None):
				currentdata['url_boxart'] = game[15]
			if (game[15] != None):
				currentdata['url_boxart'] = game[16]
			if (game[16] != None):
				currentdata['url_fanart'] = game[17]
			if (game[17] != None):
				currentdata['url_screen'] = game[18]
			if (game[18] != None):
				currentdata['url_banner'] = game[19]

		else:
			currentdata = None

		gameParams = FetchDataForId(game[3], fileTitle, game[7], currentdata)

		if ('scanned' in gameParams):

			fields = gameParams.keys()
			values = gameParams.values()
			fieldlist = " = (?),".join(fields)

			values.append(game[1])
			values.append(game[7])

			if (game[2] == None):
				sqlupdate = "UPDATE games SET %s = (?) WHERE filename = (?) and console = (?) and filename_archive is Null;" % (fieldlist)
			else:
				values.append(game[2])
				sqlupdate = "UPDATE games SET %s = (?) WHERE filename = (?) and console = (?) and filename_archive = (?);" % (fieldlist)

			SQDB.execute(sqlupdate, values)

	SQDB.commit()
	return MessageContainer(L("MSG_TITLE_SUCCESS"), L("DB_REFRESH_INFO"))

####################################################################################################
#	Loop through our current db and check if roms still exist
#	Check the mame list as well so roms with non-working status are removed
####################################################################################################
def CleanUpRoms():
	for game in SQDB.execute("SELECT filename, console, filename_archive FROM games;"):
		gamePath = os.path.join(Prefs['ROM_ROOT'], game[1], game[0])
		file_extension = os.path.splitext(game[0])[1].lower()
		if ( (not os.path.exists(gamePath)) or (file_extension not in GetExtensionForEmulators(game[1].lower()) ) ):
			if ( file_extension == ".app" and os.path.exists(gamePath + '/') ):
				continue

			Log("EDIT: Removing game: %s" % (game[0]))

			if (game[2] == None):
				SQDB.execute('DELETE FROM games WHERE filename = ? AND console = ? AND filename_archive is Null', [game[0], game[1]])
			else:
				SQDB.execute('DELETE FROM games WHERE filename = ? AND console = ? AND filename_archive = ?', [game[0], game[1], game[2]])
		else:
			if (game[2] != None):
			# Check to see if the archive still holds the same contents we think
				if ( game[2] not in GetArchiveContents(gamePath) ):
					# Not nice, the archive has been altered and file was removed.
					Log("EDIT: Removing game: %s, archive was altered" % (game[0]))
					SQDB.execute('DELETE FROM games WHERE filename = ? AND console = ? AND filename_archive = ?;', game)

	SQDB.commit()

	# if (Prefs['MAMEDB_LIST']):
	# 	# clean up the roms that are not in approved list we created and somehow did end up in the SQDB
	# 	try:
	# 		SQDB.commit()
	# 		for game in SQDB.execute("SELECT filename_rom FROM (SELECT filename_rom FROM games WHERE console = 'MAME' EXCEPT SELECT filename_rom FROM mame);"):
	# 			Log("EDIT: Removing game: " +game[0] + " it is removed from the approved list")
	# 			SQDB.execute("DELETE FROM games WHERE filename_rom = ? AND console = 'MAME';", game)
	# 		SQDB.commit()
	# 	except SQDB.Error, e:
	# 		Log('Sqlite error:' + e.args[0] + ' do not worry, we corrected the problem.')

####################################################################################################
#	Recursive search for roms, exclude unwanted dirs
####################################################################################################
def SearchAll(title, query=None):
	oc = ObjectContainer(title2=title)
	if (query == "players"):

		#SELECT (CASE WHEN games.players is not Null THEN games.players ELSE mame.players END) playa,* FROM games LEFT OUTER JOIN mame ON games.filename_rom = mame.filename_rom WHERE  (filename_disknr is Null or filename_disknr = 1) GROUP BY playa;
		for players in SQDB.execute("SELECT (CASE WHEN games.players is not Null THEN games.players ELSE mame.players END) as combined,* FROM games LEFT OUTER JOIN mame ON games.filename_rom = mame.filename_rom WHERE (filename_disknr is Null or filename_disknr = 1) AND combined is not Null and combined != '' GROUP BY combined;"):
			oc.add(DirectoryObject(key = Callback(GetListForType, query=players[0], cat=query), title=str(players[0]) + " player") )

	if (query == "buttons"):
		for buttons in SQDB.execute('SELECT DISTINCT buttons FROM mame,games WHERE mame.filename_rom = games.filename_rom AND buttons != \'\' AND (filename_disknr is Null or filename_disknr = 1) ORDER BY buttons;'):
			oc.add(DirectoryObject(key = Callback(GetListForType, query=buttons[0], cat=query), title=buttons[0] + " button") )
	if (query == "controller"):
		for controller in SQDB.execute('SELECT DISTINCT controller FROM mame,games WHERE mame.filename_rom = games.filename_rom AND controller != \'\' AND (filename_disknr is Null or filename_disknr = 1) ORDER BY controller;'):
			oc.add(DirectoryObject(key = Callback(GetListForType, query=controller[0], cat=query), title=controller[0].capitalize()) )
	if (query == "orientation"):
		for orientation in SQDB.execute('SELECT DISTINCT orientation FROM mame,games WHERE mame.filename_rom = games.filename_rom AND orientation != \'\' AND (filename_disknr is Null or filename_disknr = 1) ORDER BY orientation;'):
			if(orientation[0] == 0):
				game = "Horizontal"
			else:
				game = "Vertical"
			oc.add(DirectoryObject(key = Callback(GetListForType, query=orientation[0], cat=query), title=game) )
	# if (query == "board"):
	# 	for board in SQDB.execute('SELECT DISTINCT board FROM mame,games WHERE mame.filename_rom = games.filename_rom AND board != \'\' AND (filename_disknr is Null or filename_disknr = 1) ORDER BY board;'):
	# 		oc.add(DirectoryObject(key = Callback(GetListForType, query=board[0], cat=query), title=board[0]) )

	if (query == "genre"):
		for genre in SQDB.execute("SELECT DISTINCT genre FROM games WHERE genre NOT NULL AND (filename_disknr is Null or filename_disknr = 1) ORDER BY genre;"):
			genrethumb=re.sub(os.path.sep, '-', genre[0])
			oc.add(DirectoryObject(key = Callback(GetListForType, query=genre[0], cat=query), title=genre[0], thumb=R("genre_" + genrethumb.replace(' ','-')+".png")) )

	if (query == "year"):
		for year in SQDB.execute("SELECT DISTINCT year FROM games WHERE year NOT NULL AND (filename_disknr is Null or filename_disknr = 1) ORDER BY year;"):
			oc.add(DirectoryObject(key = Callback(GetListForType, query=year[0], cat=query), title=year[0]) )

	if (query == "publisher"):
		for publisher in SQDB.execute("SELECT DISTINCT publisher FROM games WHERE publisher NOT NULL AND (filename_disknr is Null or filename_disknr = 1) ORDER BY publisher;"):
			oc.add(DirectoryObject(key = Callback(GetListForType, query=publisher[0], cat=query), title=publisher[0]) )

	if (query == "developer"):
		for developer in SQDB.execute("SELECT DISTINCT developer FROM games WHERE developer NOT NULL AND (filename_disknr is Null or filename_disknr = 1) ORDER BY developer;"):
			oc.add(DirectoryObject(key = Callback(GetListForType, query=developer[0], cat=query), title=developer[0]) )

	return oc

def GetListForType(cat=None, query=None, favorite=None):
	oc = ObjectContainer()

	sql = "SELECT games.filename, title, console, description, developer, publisher, games.year, games.genre, (CASE WHEN url_boxart is not Null THEN url_boxart ELSE url_screen END) as boxart, url_fanart, games.filename_archive FROM games"
	if (cat == "players"):
		sql = "SELECT games.filename, title, console, description, developer, publisher, games.year, games.genre, url_boxart, url_fanart, url_screen, games.filename_archive FROM games LEFT OUTER JOIN mame ON mame.filename_rom = games.filename_rom WHERE (filename_disknr is Null or filename_disknr = 1) AND (mame.players = ? OR games.players = '%s') ORDER BY title ;" % (query)
	if (cat == "buttons"):
		sql += ",mame WHERE mame.filename_rom = games.filename_rom AND (filename_disknr is Null or filename_disknr = 1) AND buttons = ? ORDER BY title ;"
	if (cat == "controller"):
		sql += ",mame WHERE mame.filename_rom = games.filename_rom AND (filename_disknr is Null or filename_disknr = 1) AND controller = ? ORDER BY title ;"
	if (cat == "orientation"):
		sql += ",mame WHERE mame.filename_rom = games.filename_rom AND (filename_disknr is Null or filename_disknr = 1) AND orientation = ? ORDER BY title ;"
	if (cat == "board"):
		sql += ",mame WHERE mame.filename_rom = games.filename_rom AND (filename_disknr is Null or filename_disknr = 1) AND board = ? ORDER BY title ;"

	#Log(sql)

	if (cat == "genre"):
		sql += " WHERE genre= ? ORDER BY title ;"
	if (cat == "year"):
		sql += " WHERE year = ? ORDER BY title ;"
	if (cat == "publisher"):
		sql += " WHERE publisher = ? ORDER BY title ;"
	if (cat == "developer"):
		sql += " WHERE developer = ? ORDER BY title ;"

	for game in SQDB.execute(sql, [query]):
		subtitle=game[2]
		if game[6] != None:
			if subtitle != "":
				subtitle += " - "
			subtitle += "%s" % (game[6])
		if game[7] != None:
			if subtitle != "":
				subtitle += " - "
			subtitle += game[7]

		if ( Prefs['ENABLE_FAVORITES'] or ( GetDiskInfo(game[0]) and (GetEmulatorForSystem(game[2], game[0]) != 'fsuae') ) ):
			if (Prefs['SCRAPE_FANART']):
				oc.add(PopupDirectoryObject(key = Callback(FavoritesMenu, console=game[2], rom=game[0], archive=game[10]), title=game[1], summary=game[3], thumb=game[8], art=game[9]) )
			else:
				oc.add(PopupDirectoryObject(key = Callback(FavoritesMenu, console=game[2], rom=game[0], archive=game[10]), title=game[1], summary=game[3], thumb=game[8]) )
		else:
			if (Prefs['SCRAPE_FANART']):
				oc.add(DirectoryObject(key = Callback(StartGame, console=game[2], rom=game[0], archive=game[10]), title=game[1], summary=game[3], thumb=game[8], art=game[9]) )
			else:
				oc.add(DirectoryObject(key = Callback(StartGame, console=game[2], rom=game[0], archive=game[10]), title=game[1], summary=game[3], thumb=game[8]) )

	return oc

####################################################################################################
def UpdateFavorites(rom, console, archive, action=None):
	if (archive == None):
		sqladd = 'UPDATE games SET favorite = 1 WHERE filename = ? AND console = ? AND filename_archive is Null;'
		sqldel = 'UPDATE games SET favorite = 0 WHERE filename = ? AND console = ? AND filename_archive is Null;'
		values = [rom, console]
	else:
		sqladd = 'UPDATE games SET favorite = 1 WHERE filename = ? AND console = ? AND filename_archive = ?;'
		sqldel = 'UPDATE games SET favorite = 0 WHERE filename = ? AND console = ? AND filename_archive = ?;'
		values = [rom, console, archive]

	if (action == "add"):
		SQDB.execute(sqladd, values)
		SQDB.commit()
		return MessageContainer(L("MSG_TITLE_SUCCESS"), L("ADDED_TO_FAVORITES"))
	else:
		SQDB.execute(sqldel, values)
		SQDB.commit()
		return MessageContainer(L("MSG_TITLE_SUCCESS"), L("REMOVED_FROM_FAVORITES"))

####################################################################################################
@route(PREFIX + '/favoritesmenu')
def FavoritesMenu(title, console, rom, archive):
	oc = ObjectContainer(title2 = title)

	# first check for diskinfo
	diskInfo = GetDiskInfo(rom)
	# Reload the config files so we have accurate data
	LoadConfigFiles()
	# get the emulator that is chosen for the rom extension so we can see if has multidisk support
	emulator = GetEmulatorForSystem(console, rom)

	if (diskInfo and emulator != 'fsuae'):
		for game in GetMultiDisk(console, rom):
			multiDiskInfo = GetDiskInfo(game)
			oc.add(DirectoryObject(
				key = Callback(StartGame, console=console, rom=rom, archive=archive),
				title="Start "+multiDiskInfo['text']+ " "+str(multiDiskInfo['number'])))
	else:
		oc.add(DirectoryObject(
			key = Callback(StartGame, console=console, rom=rom, archive=archive),
			title="Start game"))

	if (archive):
		for game in SQDB.execute("SELECT favorite,url_trailer FROM games WHERE filename = ? and console = ? and filename_archive = ? ;", [rom, console, archive]):
			if (Prefs['ENABLE_FAVORITES']):
				if (game[0] == 0 or game[0] == None):
					oc.add(DirectoryObject(
						key = Callback(UpdateFavorites, action="add", console=console, rom=rom, archive=archive),
						title=L("MENU_ADD_TO_FAVORITES")))
				else:
					oc.add(DirectoryObject(
						key = Callback(UpdateFavorites, action="remove", console=console, rom=rom, archive=archive),
						title = L("MENU_REM_FROM_FAVORITES")))
				#if (game[1]):
				#	dir.Append(Function(WebVideoItem(PlayVideo, title=L("WATCH_TRAILER")), pageUrl=game[1]))
	else:
		for game in SQDB.execute("SELECT favorite,url_trailer FROM games WHERE filename = ? and console = ? and filename_archive is Null ;", [rom, console]):
			if (Prefs['ENABLE_FAVORITES']):
				if (game[0] == 0 or game[0] == None):
					oc.add(DirectoryObject(
						key = Callback(UpdateFavorites, action="add", console=console, rom=rom, archive=archive),
						title=L("MENU_ADD_TO_FAVORITES")))
				else:
					oc.add(DirectoryObject(
						key = Callback(UpdateFavorites, action="remove", console=console, rom=rom, archive=archive),
						title = L("MENU_REM_FROM_FAVORITES")))
				#if (game[1]):
				#	dir.Append(Function(WebVideoItem(PlayVideo, title=L("WATCH_TRAILER")), pageUrl=game[1]))

	return oc

####################################################################################################
def GetMultiDisk(console, rom):
	gameList = []
	for game in SQDB.execute("SELECT filename_rom FROM games WHERE filename = ? AND console = ? ;", [rom, console]):
		for multiDisk in SQDB.execute("SELECT filename FROM games WHERE filename_rom = ? AND console = ? ;", [game[0], console]):
			gameList.append(multiDisk[0])
	return gameList

####################################################################################################
def PlayVideo(title, pageUrl):
	YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
	YOUTUBE_FMT = [34, 18, 35, 22, 37]

	yt_page = HTTP.Request( pageUrl , cacheTime=1)

	fmt_url_map = re.findall('"url_encoded_fmt_stream_map".+?"([^"]+)', yt_page)[0]
	fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

	fmts = []
	fmts_info = {}

	for f in fmt_url_map:
		map = {}
		params = f.split('\u0026')
		for p in params:
			(name, value) = p.split('=')
			map[name] = value
		quality = str(map['itag'])
		fmts_info[quality] = String.Unquote(map['url'])
		fmts.append(quality)

	index = YOUTUBE_VIDEO_FORMATS.index('High') # fixed the display quality here
	if YOUTUBE_FMT[index] in fmts:
		fmt = YOUTUBE_FMT[index]
	else:
		for i in reversed( range(0, index+1) ):
			if str(YOUTUBE_FMT[i]) in fmts:
				fmt = YOUTUBE_FMT[i]
				break
			else:
				fmt = 5

	url = (fmts_info[str(fmt)]).decode('unicode_escape')
	Log("  VIDEO URL --> " + url)
	return Redirect(url)

####################################################################################################
@route(PREFIX + '/startrandomgame')
def StartRandomGame(title):
	for game in SQDB.execute("SELECT filename, console, filename_archive FROM games ORDER BY RANDOM() LIMIT 1;"):
		StartGame(game[1], game[0], game[2])

####################################################################################################
def StartGame(console, rom, archive):

	Log("%s %s %s " % (console, rom, archive))

	if (not os.path.isdir(Prefs['EMU_ROOT'])):
		return MessageContainer(L("MSG_TITLE_ERROR"), L("Emulator dir "+Prefs['EMU_ROOT']+" does not exist."))

	gamePath = os.path.join(Prefs['ROM_ROOT'],console,rom)
	extraParams = ""
	if console in ['Nintendo 64']:
		if (rom.lower().find("[glide]") > -1 or rom.lower().find("[glide64]") > -1 or rom.lower().find("(glide)") > -1 or rom.lower().find("(glide64)") > -1):
			extraParams = "glide64"
		elif (rom.lower().find("[arach]") > -1 or rom.lower().find("[arachnoid]") > -1 or rom.lower().find("(arach)") > -1 or rom.lower().find("(arachnoid)") > -1):
			extraParams = "arachnoid"
		else:
			extraParams = "rice"

	# Check how many roms are in the archive that we support
	for count in SQDB.execute("SELECT COUNT(filename) FROM games WHERE filename = ? AND console = ?;", [rom, console]):
		multiarchive = count[0]

	# Get the first emulator capable of running the rom and the extensions it supports
	if (archive != None):
		emulator = GetEmulatorForSystem(console, archive)
	else:
		emulator = GetEmulatorForSystem(console, rom)

	if (emulator == None):
		return MessageContainer(L("MSG_TITLE_ERROR"), "We cannot find a suitable emulator for this filetype: " + os.path.splitext(rom)[1].lower())
	else:
		emulatorCapabilities = EMULATORS[emulator]

	# Check if the emulator is capable of launching the rom on it's own ( natively support archived files )
	cleanup = None
	if ( (archive != None and (os.path.splitext(rom)[1] not in emulatorCapabilities) ) or (multiarchive > 1) ):
		Log('Init archive extraction')
		tmpPath = os.getenv('TMPDIR')
		if (not tmpPath):
			tmpPath = os.getenv('TMP')
		if (not tmpPath):
			tmpPath = os.getenv('TEMP')
		if (not tmpPath):
			tmpPath = os.getenv('/var/tmp')
		archivePath = os.path.join(tmpPath, archive)
		archiveFile = zipfile.ZipFile(gamePath)

		extractdir = archiveFile.extract(archive, archivePath)

		rom=archive
		gamePath=extractdir
		cleanup = True

	if (Prefs['PREVIEW_CONTROLS'] and console.lower() in SYSTEMS_LIST['systems']['arcade']):
		for game in SQDB.execute("SELECT filename_rom, title FROM games WHERE filename = ? AND console= ? ;", [rom, console]):
			romname = game[0]
			gamename = game[1].replace(' ', '_').lower()
			FetchControllerData(romname, gamename)

	multiDisk = []
	for multi in GetMultiDisk(console, rom):
		 multiDisk.append(os.path.join(Prefs['ROM_ROOT'],console, multi))
	multiDisk = ";".join(multiDisk)

	Log("STARTING EMU: " +emulator+ " for console: " +console+ " with ROM:" + gamePath)
	Log("EMU PATH IS: " + os.path.join(Prefs['EMU_ROOT'], 'Emulators/'))
	# Log(Helper.Run("_run_emulator.sh", emulator, CODE_DIR, gamePath, os.path.join(Prefs['EMU_ROOT'], ''), console.lower(), multiDisk, extraParams))
	Log(Helper.Run(emulator+".sh", gamePath, os.path.join(Prefs['EMU_ROOT'], 'Emulators/'), console.lower(), multiDisk, extraParams))

	# Looks like we don't need it anymore ...
	# Cleanup time
	# if (cleanup != None):
	# 	os.remove(extractdir)

####################################################################################################
#		Get the list of known extensions for each emulator combined by system
####################################################################################################
def GetEmulatorForSystem(console, rom):
	console = console.lower()
	extension = os.path.splitext(rom)[1].lower()
	for systemtype in SYSTEMS_LIST['systems']:
		for system in SYSTEMS_LIST['systems'][systemtype]:
			if (console == system):
				for emulator in SYSTEMS_LIST['systems'][systemtype][system]:
 					if (extension in EMULATORS[emulator]):
						return emulator

####################################################################################################
@route(PREFIX + '/search/rom')
def SearchForRom(title, query=None):
	Log("Searching: " + query)
	if query != None:
		search = []
		search.append(query)
		try:
			dir = MediaContainer(title2=title)
			result = SQDB.execute("SELECT * FROM games WHERE filename LIKE '%" + query + "%' OR publisher LIKE '%" + query + "%' AND (filename_disknr is Null or filename_disknr = 1) ORDER BY title;")
			count = result.fetchall()
			if (len(count) > 0):
				for game in count:
					subtitle=game[7]
					if game[12] != None:
						if subtitle != "":
							subtitle += " - "
						subtitle += "%s" % (game[12])
					if game[13] != None:
						if subtitle != "":
							subtitle += " - "
						subtitle += game[13]

					if (game[16] == None):
						boxart = game[18]
					else:
						boxart = game[16]

					if (Prefs['ENABLE_FAVORITES'] or (GetDiskInfo(game[1]) and (GetEmulatorForSystem(game[7], game[1]) != 'fsuae'))):
						if (Prefs['SCRAPE_FANART']):
							oc.add(PopupDirectoryObject(
								key = Callback(FavoritesMenu, title=game[8], console=game[7], rom=game[1], archive=game[2]),
								title=game[8], summary=game[9], tagline=subtitle, thumb=boxart, art=game[17]))
						else:
							oc.add(PopupDirectoryObject(
								key = Callback(FavoritesMenu, title=game[8], console=game[7], rom=game[1], archive=game[2]),
								title=game[8], summary=game[9], tagline=subtitle, thumb=boxart))
					else:
						if (Prefs['SCRAPE_FANART']):
							oc.add(DirectoryObject(
								key = Callback(StartGame, console=game[7], rom=game[1], archive=game[2]),
								title=game[8], summary=game[9], thumb=boxart, art=game[17]))
						else:
							oc.add(DirectoryObject(
								key = Callback(StartGame, console=game[7], rom=game[1], archive=game[2]),
								title=game[8], summary=game[9], thumb=boxart))

				return oc
			else:
				return MessageContainer(L("MSG_TITLE_ERROR"), L("SRCH_NORESULTS"))
		except:
			return MessageContainer(L("MSG_TITLE_ERROR"), L("SRCH_FAILED"))

####################################################################################################
@route(PREFIX + '/allgames')
def GetAllGamesList(title, cat=None):
	if (cat == 'favorites'):
		sql = "SELECT * FROM games WHERE favorite = 1 AND (filename_disknr is Null or filename_disknr = 1) ORDER BY title;"
	else:
		sql = "SELECT * FROM games WHERE (filename_disknr is Null or filename_disknr = 1) ORDER BY title;"

	oc = ObjectContainer(title2 = title)

	subtitles = ""

	for game in SQDB.execute(sql):
		subtitle=game[7]
		if game[12] != None:
			if subtitle != "":
				subtitle += " - "
			subtitle += "%s" % (game[12])
		if game[13] != None:
			if subtitle != "":
				subtitle += " - "
			subtitle += game[13]

		if (game[16] == None):
			boxart = game[18]
		else:
			boxart = game[16]

		if (Prefs['ENABLE_FAVORITES'] or (GetDiskInfo(game[1]) and (GetEmulatorForSystem(game[7], game[1]) != 'fsuae'))):
			if (Prefs['SCRAPE_FANART']):
				oc.add(PopupDirectoryObject(
					key = Callback(FavoritesMenu, title=game[8], console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], tagline=subtitle, thumb=boxart, art=game[17]))
			else:
				oc.add(PopupDirectoryObject(
					key = Callback(FavoritesMenu, title=game[8], console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], tagline=subtitle, thumb=boxart))
		else:
			if (Prefs['SCRAPE_FANART']):
				oc.add(DirectoryObject(
					key = Callback(StartGame, console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], thumb=boxart, art=game[17]))
			else:
				oc.add(DirectoryObject(
					key = Callback(StartGame, console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], thumb=boxart))

	return oc

####################################################################################################
@route(PREFIX + '/allsystems')
def GetSystemList(title, system):
	oc = ObjectContainer(title2 = title)

	str = ""
	for system in SYSTEMS_LIST['systems'][system]:
		str += " OR lower(console) == '" + system + "'"

	for console in SQDB.execute("SELECT DISTINCT console FROM games WHERE " + str[3:] + " ORDER BY console;"):
		background=re.sub(' ', '-', "systems_" + console[0] + ".png")
		oc.add(DirectoryObject(key = Callback(GetListForConsole, console=console[0]), title=console[0], thumb=R(background)))

	return oc

####################################################################################################
@route(PREFIX + '/allconsoles')
def GetConsoleList(title):
	oc = ObjectContainer(title2 = title)
	for console in SQDB.execute("SELECT DISTINCT console FROM games ORDER BY console;"):
		background=re.sub(' ', '-', "systems" + os.path.sep + console[0] + ".png")
		oc.add(DirectoryObject(key = Callback(GetListForConsole, console=console[0]), title=console[0], thumb=R(background)))
	return oc

####################################################################################################
@route(PREFIX + '/games/console')
def GetListForConsole(console):

	oc = ObjectContainer(title2 = console, view_group = 'MediaPreview')

	for game in SQDB.execute("SELECT * FROM games WHERE console = ? AND (filename_disknr is Null or filename_disknr = 1) ORDER BY title;", [console]):
		subtitle=""
		if game[10] != None:
			subtitle += game[10]
		if game[11] != None:
			if subtitle != "":
				subtitle += " / "
			subtitle += game[11]
		if (game[12] != None):
			try:
				subtitle += ' - ' + str(int(game[12]))
			except ValueError:
				subtitle += ''
		if game[13] != None:
			if subtitle != "":
				subtitle += " - "
			subtitle += game[13]

		if (game[16] == None):
			boxart = game[18]
		else:
			boxart = game[16]

		try:
			if (game[12] != None):
				year = int(game[12])
			else:
				year = int()
		except ValueError:
			year = int()

		#, rating_key=md5.new(game[7]+game[6]).hexdigest()

		if (Prefs['ENABLE_FAVORITES'] or (GetDiskInfo(game[1]) and (GetEmulatorForSystem(game[7], game[1]) != 'fsuae'))):
			if (Prefs['SCRAPE_FANART']):
				oc.add(PopupDirectoryObject(
					key = Callback(FavoritesMenu, title=game[8], console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], tagline=subtitle, thumb=boxart, art=game[17], duration=game[0]))
			else:
				oc.add(PopupDirectoryObject(
					key = Callback(FavoritesMenu, title=game[8], console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], tagline=subtitle, thumb=boxart, duration=game[0]))
		else:
			if (Prefs['SCRAPE_FANART']):
				oc.add(DirectoryObject(
					key = Callback(StartGame, console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], thumb=boxart, art=game[17], duration=game[0]))
			else:
				oc.add(DirectoryObject(
					key = Callback(StartGame, console=game[7], rom=game[1], archive=game[2]),
					title=game[8], summary=game[9], thumb=boxart, duration=game[0]))

	return oc

####################################################################################################
def FetchControllerData(romname, gamename):

	# Retrieve the game info we can find, without it we have no need to continue since we can't map anyway
	try:
		page = XML.ElementFromURL("file://" + os.path.join(Prefs['EMU_ROOT'], 'CPanel/configs/controls.xml'))
		players = page.xpath('//game[@romname="'+ romname +'"]/@numPlayers')									# get the nr of players reported ( this can differ from mame )
		controls = page.xpath('//game[@romname="'+ romname +'"]/player/controls/control/constant')				# get the name of the controller e.g. joy4way
		ctype = page.xpath('//game[@romname="'+ romname +'"]/player/controls/control[contains(@name,"iag")]')	# some controllers have a bit of etra info wether it's diagonal or not.
		buttonsname = page.xpath('//game[@romname="'+ romname +'"]/player[@number="1"]/labels/label/@name')		# get all assigned labels ( buttons and controller directions )
		buttonsvalue = page.xpath('//game[@romname="'+ romname +'"]/player[@number="1"]/labels/label/@value')	# get all assigned value ( buttons and controller directions )
		description = page.xpath('//game[@romname="'+ romname +'"]/miscDetails/text()')
	except:
		Log("WARNING: controls.xml not found in: "+ os.path.join(Prefs['EMU_ROOT'], 'CPanel/configs/controls.xml'))
		return False

	try:
		description = description[0].strip().replace(' ', '_')
		description = cleanupControllerPreviewText(textwrap.fill(description, width=300)).replace('\n', ';')
	except:
		pass

	# Test if we found controller information, without it we bail
	if (len(buttonsname) == 0):
		Log("DEBUG: Sorry no controller data found in controls.xml for rom: " +romname)
		return False

	# Fetch our own controllerdata if we have it, if not .... skip the rest
	try:
		controller = Prefs['CONTROLLER'].lower()
		ctrlown = XML.ElementFromURL("file://" + os.path.join(Prefs['EMU_ROOT'], "CPanel/configs/controllers.xml"))
		ctrls = ctrlown.xpath('//'+controller+'/button/@name')
		ports = ctrlown.xpath('//'+controller+'/button/@value')
		locs =  ctrlown.xpath('//'+controller+'/button/@location')
	except:
		Log("WARNING: controllers.xml not found in mame directory")
		return False

	if (len(ctrls) == 0):
		Log("DEBUG: Sorry no controller data found in cotrollers.xml")
		return False

	# Next, get all data we can from the cfg files
	controlsdict = dict()
	controlsdict = FetchControllerDataMame('CPanel/configs/controls_default.xml', controlsdict)	# grab the default mame config
	controlsdict = FetchControllerDataMame('MAME/cfg/default.cfg', controlsdict)		# grab the default config we created inside mame
	controlsdict = FetchControllerDataMame('MAME/cfg/'+romname+'.cfg', controlsdict)	# grab the per game override controls

	if (players):
		players = players[0]
	else:
		players = "unknown"

	# # Controller type is only of interest when using an actual arcade joystick, for gamepad we just look at the labels for the correct mappings
	# totcontrols = ""
	# if (controls):
	#  	for element in controls:
	#  		conelement = XML.StringFromObject(element)
	#  		totcontrols = re.search("name=\"(.*)\"", conelement).group(1)
	#  		#Log("Controls found: " + totcontrols)
	# else:
	#  	Log("No controller type found")
	#
	# if (ctype):
	# 	totcontrols += "d" # ctype only filters on diagonal for 4 way joy

	#Log(controlsdict)

	controlstextloc = ""
	controlstextlab = ""
	controlstextbut = ""
	unassignedcontrols = ""
	tempcontrolslist = list()
	tempbuttonassignmentlist = list()
	# Loop through the controls.xml file ( we start doing that here because there are some descrepancies between the name tags and we can correct them here)
	for mamecontrolbutton, controllabel in map(None, buttonsname, buttonsvalue):
		mamematchtitle = mamecontrolbutton + "|standard"

		# rename some exceptions from the controls.xml file
		# TODO: make the list of exceptions complete
		if (mamecontrolbutton == "P1_PADDLE"):
			mamematchtitle = "P1_PADDLE|decrement"
		if (mamecontrolbutton == "P1_PADDLE_EXT"):
			mamematchtitle = "P1_PADDLE|increment"
		if (mamecontrolbutton == "P1_DIAL"):
			mamematchtitle = "P1_DIAL|decrement"
		if (mamecontrolbutton == "P1_DIAL_EXT"):
			mamematchtitle = "P1_DIAL|increment"

		# Retrieve the buttons for a specific control
		mamecontrols = controlsdict.get(mamematchtitle)

		# Check if can find the button listed in mame.cfg file
		if (mamecontrols):
			# Get the list of buttons from mame that are tied to it
			controllerbuttons = mamecontrols.split('|')
			# For each of the buttons check if we have a match with one of our controller buttons
			# for ctrl, port, loc in map(None, ctrls, ports, locs):
			for ctrl, port, location in map(None, ctrls, ports, locs):
				if (port in controllerbuttons):
					if (len(location) > 0):
						if (port not in tempcontrolslist):
							tempcontrolslist.append(port)
							tempbuttonassignmentlist.append(mamecontrolbutton)
							controlstextbut += ctrl+";"
							controlstextloc += location+";"
							controlstextlab += cleanupControllerPreviewText(controllabel) +";"
							Log("DEBUG: Found "+port+" mapped to button: "+mamecontrolbutton+" label: " +controllabel+ " location: " +location)
						else:
							Log("WARNING: Button assignment overlap detected of: "+port+ " in mame control: "+mamecontrolbutton)
					else:
						Log("NOTICE: Button: "+port+ " is assigned but doesn't have a location mapped to it, so it's probably unusable")
		else:
			Log("WARNING: Button: " +mamecontrolbutton+ " from controls.xml cannot be traced back in any of the mame .cfg files")

	for mamecontrolbutton, controllabel in map(None, buttonsname, buttonsvalue):
		if 	(mamecontrolbutton not in tempbuttonassignmentlist):
			unassignedcontrols += mamecontrolbutton+";"
			Log("WARNING: Unbound button detected: " +mamecontrolbutton+ " is not configured in mame")

	Log("DEBUG: Found all the data we need, generating controller image")
 	Log(Helper.Run("_controlpanel_fullscr.sh", cleanupControllerPreviewText(gamename), os.path.join(Prefs['EMU_ROOT'], 'Emulators/'), players, controlstextloc, controlstextlab, controller, controlstextbut.lower(), unassignedcontrols, description))

####################################################################################################
def FetchControllerDataMame(filename, controlsdict):
	try:
		# grab the default mame controls from controls_default.xml
		ctrlmame = XML.ElementFromURL("file://" + os.path.join(Prefs['EMU_ROOT'], filename))
		ports = ctrlmame.xpath('//input/port')
		for name in ports:
			for nseq in name:
				controlsdict.update( { name.get('type') + "|" + nseq.get('type') : nseq.text.strip().replace(' OR ', '|') } )
	except:
		Log("DEBUG: Unable to read: " + filename)

	return controlsdict

####################################################################################################
def cleanupControllerPreviewText(name):
	name = name.replace('/','-').replace('\\','-')
	name = name.replace('\'','').replace('"','')
	name = name.replace('(','').replace(')','')
	name = name.replace('[','').replace(']','')
	name = name.replace('{','').replace('}','')
	name = name.replace(',','').replace('.','')
	name = name.replace(';','').replace(':','')
	name = name.replace('+',' and ')
	name = name.replace(' ','_')
	return name

####################################################################################################
def decToRoman(num,s, decs, romans):

	"""
	  convert a Decimal number to Roman numeral recursively
	  num: the decimal number
	  s: the roman numerial string
	  decs: current list of decimal denomination
	  romans: current list of roman denomination
	"""

	if decs:
	  if (num < decs[0]):
	    # deal with the rest denomination
	    return decToRoman(num,s,decs[1:],romans[1:])
	  else:
	    # deduce this denomation till num<desc[0]
	    return decToRoman(num-decs[0],s+romans[0], decs, romans)
	else:
	  # we run out of denomination, we are done
	  return s

####################################################################################################
def sanitizeGenre(genre):
	if ( genre != None ):
		genre = genre.lower()

		found = re.findall('various', genre)
		if (found):
			genre = 'miscellaneous'

		found = re.findall('beat', genre)
		if (found):
			genre = 'beat em up'

		found = re.findall('flipper', genre)
		if (found):
			genre = 'pinball'

		found = re.findall('adventure', genre)
		if (found):
			genre = 'adventure'
		found = re.findall('strategy', genre)
		if (found):
			genre = 'strategy'
		found = re.findall('simulation', genre)
		if (found):
			genre = 'simulation'

		found = re.findall('guide', genre)
		if (found):
			genre = 'driving'
		found = re.findall('vehicular', genre)
		if (found):
			genre = 'driving'
		found = re.findall('race', genre)
		if (found):
			genre = 'driving'

		found = re.findall('fitnes', genre)
		if (found):
			genre = 'sport'

		found = re.findall('rpg', genre)
		if (found):
			genre = 'role-playing'

		found = re.findall('fps', genre)
		if (found):
			genre = 'first-person shooter'


		found = re.findall('multi', genre)
		if (found):
			genre = 'mini games'

		found = re.findall('pace', genre)
		if (found):
			genre = 'rhythm'

		# Most global escapes
		found = re.findall('person', genre)
		if (found):
			genre = 'first-person shooter'
		found = re.findall('fighting', genre)
		if (found):
			genre = 'fighting'

		found = re.findall('mini', genre)
		if (found):
			genre = 'mini games'
		found = re.findall('platform', genre)
		if (found):
			genre = 'platform'
		found = re.findall('misc', genre)
		if (found):
			genre = 'miscellaneous'
		found = re.findall('shoot', genre)
		if (found):
			genre = 'shooter'
		found = re.findall('quiz', genre)
		if (found):
			genre = 'quiz'
		found = re.findall('puzzle', genre)
		if (found):
			genre = 'puzzle'
		found = re.findall('role', genre)
		if (found):
			genre = 'role-playing'
		found = re.findall('driving', genre)
		if (found):
			genre = 'driving'
		found = re.findall('action', genre)
		if (found):
			genre = 'action'
		found = re.findall('board', genre)
		if (found):
			genre = 'board games'
		found = re.findall('table', genre)
		if (found):
			genre = 'table games'
		found = re.findall('sport', genre)
		if (found):
			genre = 'sports'

		genre = genre.capitalize()
	return genre

def sanitizePubl(publisher):
	if  ( publisher is not None ):
		publisher = publisher.split('[')[0].split('(')[0].strip()
		test = re.search('^/(.+)', publisher)
		if (test):
			publisher = test.group(1).strip()
	return publisher

def sanitizeDescr(description=None):
	return description

def stripReleaseInfo(name):
	name = name.lower()
	name = name.split('[')[0].split('(')[0].rstrip()
	name = name.replace('_', '').replace('-', '').replace('/', '').replace('\\', '').replace("'", '').replace('"', '').replace('&', '')
	name = name.replace(',', '').replace('.', '').replace(':', '').replace(';', '').replace(' ', '')
	return 	name

def doNothing():
	return False



	# path = os.path.join(Prefs['EMU_ROOT'), 'CPanel/mamedata')
	# data = open(path + '/history.dat').read()
	# # Get the game data block from the file
	# gdata = re.search("^(\$info.*[=|,]10yard,)(.+?)^\$end", data, re.I|re.M|re.DOTALL).group(2)
	# try:
	# 	description = re.search("(.+?)\\r\\n- ", gdata, re.I|re.M|re.DOTALL).group(1)
	# 	description = description.split('\r\n')
	# 	del description[0:7]
	# 	description = "\r\n".join(description).strip()
	# 	description = re.sub("\r\n\r\n", "\r\n", description)
	# 	Log(description)
	# except:
	# 	Log("No description found")
	#
	# try:
	# 	tips = re.search("- TIPS AND TRICKS -(.+?)\\r\\n- ", gdata, re.I|re.M|re.DOTALL).group(1).strip()
	# 	tips = re.sub("\r\n\r\n", "\r\n", tips)
	# 	Log(tips)
	# except:
	# 	Log("No tips and tricks found")
	#
	# try:
	# 	page = XML.ElementFromURL("file://" + path + '/mame.xml'))
	# 	players = page.xpath('//game[@romname="'+ romname +'"]/@numPlayers')									# get the nr of players reported ( this can differ from mame )
	# 	controls = page.xpath('//game[@romname="'+ romname +'"]/player/controls/control/constant')				# get the name of the controller e.g. joy4way
	# 	ctype = page.xpath('//game[@romname="'+ romname +'"]/player/controls/control[contains(@name,"iag")]')	# some controllers have a bit of etra info wether it's diagonal or not.
	# 	buttonsname = page.xpath('//game[@romname="'+ romname +'"]/player[@number="1"]/labels/label/@name')		# get all assigned labels ( buttons and controller directions )
	# 	buttonsvalue = page.xpath('//game[@romname="'+ romname +'"]/player[@number="1"]/labels/label/@value')	# get all assigned value ( buttons and controller directions )
	# 	description = page.xpath('//game[@romname="'+ romname +'"]/miscDetails/text()')
	# except:
	# 	Log("WARNING: controls.xml not found in: "+ os.path.join(Prefs['EMU_ROOT'), 'CPanel/configs/controls.xml'))
	#
	# data = ""

