# Plex Game Launcher Plugin
# by Nudgenudge <nudgenudge@gmail.com>

import os,subprocess,re,unicodedata,urllib
from htmlentitydefs import name2codepoint


# change language sinistra.php?&amp;lang=en
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.73.11 (KHTML, like Gecko) Version/6.1.1 Safari/537.73.11', 'referer' : 'http://google.com', 'cookies' : 'emma[lang]=en'}

Capabilities = ["title", "description", "publisher", "year", "genre", "url_screen"]

API_KEY_BING = "EE849480BB4CD90ADC00771A66F66AEB0364338C"
TITLE_URL = "http://www.progettoemma.net/giocopf.php?game=%s&lang=en"
THUMB_URL = "http://www.progettoemma.net/snap/%s/0000.png"

####################################################################################################
def search(fileTitle, console=None, gameParams=None):
	Log("DEBUG: ProgettoEmma: searching for: " + fileTitle)

	grabbed = {}
	trans = None

	#pagecontent = HTML.ElementFromURL( 'http://www.progettoemma.net/sinistra.php?lang=en', encoding='iso-8859-1', headers=HTTP_HEADERS )
	#page = HTML.StringFromElement(pagecontent)
	#cookies = HTTP.CookiesForURL('http://www.progettoemma.net')
	#Log(cookies)

	#cookies = dict('emma[lang]'='en')
	#r = requests.get(TITLE_URL % (fileTitle), cookies=cookies)
	#Log(r)

	pagecontent = HTML.ElementFromURL( TITLE_URL % (fileTitle), encoding='iso-8859-1', headers=HTTP_HEADERS )
	page = HTML.StringFromElement(pagecontent)

	#Log(pagecontent)

	tempName = re.search("<h1>(.+?)</h1>", page, re.I)
	grabbed['title'] = (stripReleaseInfo(tempName.group(1)) if (tempName) else fileTitle)
	grabbed['url_screen'] = THUMB_URL % (fileTitle)

	# Description
	pattern = re.compile("tabella --(.+?)- DATI TECNICI", re.DOTALL|re.I)
	tempDescription = pattern.search(page)
	try:
		#need to do some cleaning to get rid of html chars and the likes
		gameDescr = tempDescription.group(1).replace('<br>','').strip()
		gameDescr = os.linesep.join([s for s in gameDescr.splitlines() if s])

		tempDescription = gameDescr.splitlines()
		del tempDescription[0:2]
		gameDescr = "\r\n".join(tempDescription)
		if (gameDescr == ""):
			gameDescr = None

		#if (API_KEY_BING != "" and gameDescr != None and 'description' not in gameParams):
		#	try:
		#		transcontent = HTML.ElementFromURL("http://api.microsofttranslator.com/v2/Http.svc/Translate?appId=%s&from=it&to=en&text=%s" % (API_KEY_BING, urllib.quote(gameDescr)))
		#		trans = HTML.StringFromElement(transcontent)
		#		Log(trans)
		#		pattern = re.compile('Serialization/">(.+?)</string', re.DOTALL|re.I)
		#		tempDescription = pattern.search(trans)
		#		gameDescr = urllib.unquote(tempDescription.group(1))
		#		gameDescr = htmlentitydecode(transformCharsManual(transformChars(gameDescr)))
		#	except:
		#		Log("WARNING: Encountered error while translating: %s - Response is: %s" % (description, trans) )

	except:
		gameDescr = None

	if (gameDescr):
		grabbed['description'] = gameDescr

	# Publisher
	gamePubl = re.search("Produttore: <\/b>(.+?)<br>", page, re.I)
	if (gamePubl):
		grabbed['publisher'] = gamePubl.group(1).strip()

	# Release date
	gameDate = re.search("produzione:<\/b>(.+?)<br>", page, re.I)
	if (gameDate):
		grabbed['year'] = gameDate.group(1).strip()

	# Genre
	gameGenre = re.search("Genere del gioco:<\/b>(.+?)<br>", page, re.I)
	if (gameGenre):
		gameGenre = gameGenre.group(1).strip()

	#if (API_KEY_BING != "" and gameGenre != None and 'genre' not in gameParams):
	#	try:
	#		transcontent = HTML.ElementFromURL( "http://api.microsofttranslator.com/v2/Http.svc/Translate?appId=%s&text=%s&from=it&to=en" % (API_KEY_BING, urllib.quote(gameGenre)) )
	#		trans = HTML.StringFromElement(transcontent)
	#
	#		gameGenre = htmlentitydecode(transformCharsManual(transformChars(re.search("lization\/\">(.+?)<", trans).group(1))))
	#	except:
	#		Log("WARNING: Encoutered error while translating: %s - Response is: %s" % (gameGenre, trans) )

	if (gameGenre):
		grabbed['genre'] = gameGenre

	if (grabbed['title'] and gameGenre):
		grabbed['scanned'] = 1
		gameParams = checkMissingInfo(gameParams, grabbed)

	return gameParams

####################################################################################################
# If current results are not complete, check if we have previous data we can append to
####################################################################################################
def checkMissingInfo(gameParams, grabbed):
	if (gameParams is not None):
		for key, value in grabbed.iteritems():
			if (key in gameParams):
				if (grabbed[key] != None):
					if (grabbed[key] != ""):
						if (gameParams[key] == None):
							gameParams[key] = grabbed[key]
			else:
				if (grabbed[key] != None):
					if (grabbed[key] != ""):
						gameParams[key] = grabbed[key]
		return gameParams
	return grabbed

####################################################################################################
def stripReleaseInfo(name):
	return 	name.split('[')[0].split('(')[0].rstrip()

####################################################################################################
def compareReleaseNames(release, game):
	gameTransformed  = stripCharsRomname(release)
	releaseTransformed = stripCharsRomname(game)
	return gameTransformed == releaseTransformed

####################################################################################################
def stripCharsRomname(name):
	name = name.lower()
	name = name.split('[')[0].split('(')[0].split(u'\xa9')[0].rstrip()
	name = transformChars(name)						# strip out ISO-something chars before we start alphanumeric matching
	name = strip_accents(name)						# transform accented letters for name matching
	name = name.replace('the','')
	name = name.replace('and',' ')
	name = re.findall("(\w+)", name, re.I)					# remove all non-alphanumeric characters
	name = os.linesep.join(name)
	name = name.replace("\n","")						# remove any remaining linebreaks left in the string
	name = name.replace("\r\n","")
	name = name.replace('_','')
	name = name.strip()
	return name

####################################################################################################
# Since bing has a problem with translating single char words, we help it along a bit to make more
# readible output, mainly we just rip them out
####################################################################################################
def transformCharsManual(name):
	name = name.replace('&egrave;','is')
	name = name.replace('&nbsp;','')
	name = name.replace('&agrave;','')
	name = name.replace('&ugrave;','')
	name = name.replace('&ograve;','')
	name = name.replace('&igrave;','')
	name = name.replace('&eacute;','')
	name = name.replace('&aacute;','')
	name = name.replace('&uacute;','')
	name = name.replace('&oacute;','')
	name = name.replace('&iacute;','')
	name = name.replace('  ',' ')
	name = name.replace('  ',' ')
	return name

####################################################################################################
def transformChars(text):
	"""Removes HTML or XML character references
		and entities from a text string.
		@param text The HTML (or XML) source text.
		@return The plain text, as a Unicode string, if necessary.
		from Fredrik Lundh
		2008-01-03: input only unicode characters string.
		http://effbot.org/zone/re-sub.htm#unescape-html
		"""
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#xD":
					return unichr("\r")
				elif text[:3] == "&#x":
					return unichr(int(text[3:-1], 16))
				else:
					return unichr(int(text[2:-1]))
			except ValueError:
				Log("Value Error")
				pass
		else:
			# named entity
			# reescape the reserved characters.
			try:
				if text[1:-1] == "amp":
					text = "&"
				elif text[1:-1] == "gt":
					text = "&gt;"
				elif text[1:-1] == "lt":
					text = "&lt;"
				else:
					Log(text[1:-1])
					text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
			except KeyError:
				Log("keyerror")
				pass
		return text # leave as is
	return re.sub("&#?\w+;", fixup, text)

####################################################################################################
def htmlentitydecode(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

####################################################################################################
def strip_accents(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

####################################################################################################
#def unescape(s):
#    #"unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
#    return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)
