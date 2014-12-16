#!/usr/bin/python

from __future__ import print_function
import sys
import re
import string
import sqlite3
try:
    import xml.etree.cElementTree as xml
except ImportError:
    import xml.etree.ElementTree as xml

SQDB = sqlite3.connect('mame.sqlite', check_same_thread = False, detect_types=sqlite3.PARSE_DECLTYPES)
SQDB.text_factory = lambda x: unicode(x, "utf-8", "ignore")
SQDB.execute("drop table if exists mame")
SQDB.execute("CREATE TABLE mame (rom_id INTEGER PRIMARY KEY, \
                                filename_rom TEXT, \
                                cloneof TEXT, \
                                name TEXT, \
                                description BLOB, \
                                tips BLOB, \
                                scoring BLOB, \
                                year INTEGER, \
                                manufacturer TEXT, \
                                buttons BLOB, \
                                nrofbuttons TEXT, \
                                controller TEXT, \
                                orientation INTEGER, \
                                genre TEXT, \
                                players INTEGER, \
                                mature TEXT, \
                                status TEXT, \
                                CONSTRAINT unique_filename_rom UNIQUE (filename_rom));")
SQDB.commit()

# #TODO:
# # * fail if an unexpected state occurs

_verbose = False
_echo_file = False

controls = {}
mydoc = xml.parse('controls.xml')
for e in mydoc.findall('.//game'):
        name = e.attrib.get('romname')
        controls[name] = xml.tostring(e.find('.//player')).replace('\t','').replace('\n','')
#raise SystemExit(0)

title = {}
mydoc = xml.parse('mame.xml')
for e in mydoc.findall('.//game'):
    if (e.attrib.get('runnable') != 'no' and e.attrib.get('isbios') != 'yes'):
        name = e.attrib.get('name')
        title[name] = {}
        try:
            title[name]['title'] = e.find('.//description').text
        except:
            title[name]['title'] = None

        try:
            title[name]['year'] = e.find('.//year').text
        except:
            title[name]['year'] = None

        try:
            title[name]['manufacturer'] = e.find('.//manufacturer').text
        except:
            title[name]['manufacturer'] = None

        try:
            title[name]['cloneof'] = e.attrib.get('cloneof')
        except:
            title[name]['cloneof'] = None

        try:
            title[name]['players'] = e.find('.//input').attrib.get('players')
        except:
            title[name]['players'] = None

        try:
            title[name]['nrofbuttons'] = e.find('.//input').attrib.get('buttons')
        except:
            title[name]['nrofbuttons'] = None

        try:
            controllers = []
            for f in e.iterfind('.//input/control'):
                cont = f.attrib.get('type')
                try:
                    ways = f.attrib.get('ways')
                    if ways != None:
                        if ways.isdigit():
                            controllers.append(cont + '_' + ways + 'way')
                    else:
                        controllers.append(cont + '_' + ways)
                except:
                   controllers.append(cont)
            title[name]['controllers'] = " & ".join(controllers)
        except:
            title[name]['controllers'] = None

        try:
            title[name]['type'] = e.find('.//display').attrib.get('type')
        except:
            title[name]['type'] = None

        try:
            title[name]['rotate'] = e.find('.//display').attrib.get('rotate')
        except:
            title[name]['rotate'] = '0'

        try:
            if (e.find('.//driver').attrib.get('status') == 'good' and e.find('.//driver').attrib.get('emulation') == 'good' and e.find('.//driver').attrib.get('sound') == 'good' and e.find('.//driver').attrib.get('graphic') == 'good'):
                status = 'good'
            elif (e.find('.//driver').attrib.get('status') == 'preliminary' or e.find('.//driver').attrib.get('emulation') == 'preliminary' or e.find('.//driver').attrib.get('preliminary') == 'good' or e.find('.//driver').attrib.get('graphic') == 'preliminary'):
                status = 'preliminary'
            else:
                status = 'imperfect'
            title[name]['status'] = status
        except:
            title[name]['status'] = None

# print(title)
# raise SystemExit(0)

# Read the catlist.ini for genre matching
categories = {}
current = None
cat = open('catlist.ini')
regex = re.compile(r'\[(.+)\]')
for line in cat:
    match = regex.match(line.strip())
    if (match is not None and match.groups()[0] not in ['FOLDER_SETTINGS', 'ROOT_FOLDER']) :
        current = match.groups()[0]
    if current != None:
        categories[line.strip()] = current
# raise SystemExit(0)

# Read the nplayers.ini for nr of players supported by game
players = {}
current = None
cat = open('nplayers.ini')
regex = re.compile(r'\[(.+)\]')
for line in cat:
    match = regex.match(line.strip())
    if (match is not None and match.groups()[0] not in ['FOLDER_SETTINGS', 'ROOT_FOLDER']) :
        current = match.groups()[0]
    if current != None:
        if len(line.strip().split("=")) > 1:
            rom,player = line.strip().split("=")
            if player != '???':
                players[rom] = player
#print(categories['1942'])
#raise SystemExit(0)


# Read history.dat file and get the description, trivia and scoring text
class Game:

    regex = re.compile(r'(.+)\s+\(c\)\s+([0-9]+)\s+(.+)')

    def __init__(self, systems, romnames):
        self.systems = systems
        self.romnames = romnames
        self.bio = []
        self.descr = []
        self.technical = []
        self.trivia = []
        self.series = []
        self.scoring = []
        self.tips = []
        self.staff = []
        self.ports = []
        self.sources = []
        self.name = None
        self.publisher = None
        self.year = None
        self.current = None

    def _filter_line(self, line):
        #return line.decode('UTF-8')
        #return filter(lambda x: x in string.printable, line)
        return line

    def _add_to_bio(self, line):
        line = self._filter_line(line)
        self.bio.append(line)

        if len(self.bio) > 2:
            # split rest of bio info
            if (line.strip() == '- SOURCES -' or self.current == 'sources'):
                self.current = 'sources'
                self.sources.append(line)


            elif (line.strip() == '- PORTS -' or self.current == 'ports'):
                self.current = 'ports'
                self.ports.append(line)

            elif (line.strip() == '- STAFF -' or self.current == 'staff'):
                self.current = 'staff'
                self.staff.append(line)

            elif (line.strip() == '- SERIES -' or self.current == 'series'):
                self.current = 'series'
                self.series.append(line)

            elif (line.strip() == '- TIPS AND TRICKS -' or self.current == 'tips'):
                self.current = 'tips'
                self.tips.append(line)

            elif (line.strip() == '- SCORING -' or self.current == 'scoring'):
                self.current = 'scoring'
                self.scoring.append(line)


            elif (line.strip() == '- TRIVIA -' or self.current == 'trivia'):
                self.current = 'trivia'
                self.trivia.append(line)

            elif (line.strip() == '- TECHNICAL -' or self.current == 'technical'):
                self.current = 'technical'
                self.technical.append(line)

            else:
                self.descr.append(line)

        # name information is on the second line of the bio
        if self.name is None and len(self.bio) == 2:
            parsed = self._parse_name_info(line)
            if parsed is not None:
                self.name = parsed[0]
                self.year = parsed[1]
                self.publisher = parsed[2]

    def _parse_name_info(self, line):
        match = self.regex.match(line.strip())
        if match is not None:
            groups = match.groups()
            if len(groups) == 3:
                return groups
        if _verbose:
            print('Failed to parse info line:')
            print(line)
        return None

    def get_bio(self):
        return ''.join(self.bio)

    def get_descr(self):
        return ''.join(self.descr[1:-1])

    def get_name(self):
        return self.name

    def get_publisher(self):
        return self.publisher

    def get_year(self):
        return self.year

    def get_trivia(self):
        return ''.join(self.trivia[1:-1])

    def get_scoring(self):
        return ''.join(self.scoring[1:-1])

    def get_tips(self):
        return ''.join(self.tips[1:-1])

class StateInfo:

    def __init__(self, state):
        self.state = state

    STATE_END, STATE_GAME, STATE_BIO = range(3)

class HistDatParser:

    _known_systems = {
        'snes': 'Super Nintendo',
        'nes': 'Nintendo Entertainment System',
        'info': 'Unknown game system',
        'gba': 'Gameboy Advance',
        'n64': 'Nintendo 64',
        'gbcolor': 'Gameboy Color',
        'sg1000': 'Sega Game 1000',
        'cpc_cass': 'Amstrad CPC (Cassette)',
        'cpc_flop': 'Amstrad CPC (Floppy)',
        'bbca_cas': 'BBC Micro A (Cassette)',
        'megadriv': 'Sega Megadrive',
        'channelf': 'Fairchild Channel F',
        'a7800': 'Atari 7800',
        'a2600': 'Atari 2600',
        'crvision': '',
        'cdi': '',
        'coleco': '',
        'neogeo': '',
        'scv': '',
        'pcecd': '',
        'msx2_cart': '',
        'sms': '',
        'neocd': '',
        'vc4000': '',
        'studio2': '',
        'pce': '',
        'saturn,': '',
        'sat_cart': '',
        'aquarius': '',
        'gamegear': '',
        'coco_cart': '',
        'xegs': '',
        'x68k_flop': '',
        'gameboy': '',
        'alice32': '',
        'a5200': '',
        'a800': '',
        'advision': '',
        'c64_cart': '',
        'c64_flop': '',
        'mac_flop': '',
        'mac_hdd': '',
        'arcadia': '',
        'apfm1000': '',
        'apple2gs': '',
        'famicom_flop': '',
        'intv': '',
        'alice90': '',
        'lynx': '',
        'msx1_cart': '',
        'megacd': '',
        'megacdj': ''
    }

    _unknown_systems = set()

    def __init__(self, filename):
        self.datfile = open(filename)
        self._games_by_gamekey = {}
        self._parse()

    TOKEN_GAMEID, TOKEN_BIO, TOKEN_END = range(3)

    def _parse_token(self, line):
        parsed = None
        if line[0] is '$':
            line = line[1:]
            if line.strip() == 'end':
                parsed = [self.TOKEN_END]
            elif line.strip() == 'bio':
                parsed = [self.TOKEN_BIO]
            else:
                eqIdx = line.find('=')
                if eqIdx is not -1:
                    systemsline = line[0:eqIdx]
                    parsed = []
                    parsed.append(self.TOKEN_GAMEID)
                    systems = systemsline.strip().split(',')
                    for system in systems:
                        try:
                            self._known_systems.has_key(system)
                        except ValueError:
                            self._unknown_systems.add(system)
                    parsed.append(systems)
                    line = line[eqIdx + 1:]
                    romnames = line.strip().split(',')
                    romnames = [rom.strip()
                        for rom in romnames if len(rom) > 0]
                    parsed.append(romnames)
        return parsed

    def _parse(self):
        state_info = StateInfo(StateInfo.STATE_END)
        for line in self.datfile:
            if _echo_file:
                print(line, end='')
            parsed = self._parse_token(line)
            if state_info.state is StateInfo.STATE_END:
                if parsed is not None:
                    if parsed[0] is self.TOKEN_GAMEID:
                        game = self._add_game(parsed)
                        state_info = StateInfo(StateInfo.STATE_GAME)
                        state_info.game = game
                    elif parsed[0] is self.TOKEN_END:
                        continue
                    else:
                        raise Exception('Expected a new system after $end')
            elif state_info.state is StateInfo.STATE_GAME:
                if parsed is not None:
                    if parsed[0] is self.TOKEN_BIO:
                        game = state_info.game
                        state_info = StateInfo(StateInfo.STATE_BIO)
                        state_info.game = game
            elif state_info.state is StateInfo.STATE_BIO:
                if parsed is not None:
                    if parsed[0] is self.TOKEN_END:
                        state_info = StateInfo(StateInfo.STATE_END)
                else:
                    state_info.game._add_to_bio(line)
            else:
                raise Exception('Unexpected parse state')
        if _verbose:
            if len(self._unknown_systems) > 0:
                print("Found unknown game systems:")
                for system in self._unknown_systems:
                    print(system)

    def _get_gamekey(self, system, romname):
        return '{0}_{1}'.format(system, romname)

    def _add_game(self, parsed):
        assert parsed[0] is HistDatParser.TOKEN_GAMEID
        systems = parsed[1]
        romnames = parsed[2]
        game = Game(systems, romnames)
        for system in systems:
            for romname in romnames:
                key = self._get_gamekey(system, romname)
                self._games_by_gamekey[key] = game
        return game

    def get_game(self, system, romname):
        key = self._get_gamekey(system, romname)
        if self._games_by_gamekey.has_key(key):
            return self._games_by_gamekey[key]
        return None



    # parser = HistDatParser('history.dat')
    #g = parser.get_game('info', '88games')
    #print(g.get_descr())
    #print(parser._games_by_gamekey['info_88games'].get_descr())
    # for game in parser._games_by_gamekey:
    #     if (game.split('_')[0] == 'info'):
    #         #print('Rom: ' + game.replace('info_',''))
    #         #print(parser._games_by_gamekey[game].get_name())
    #         #print(parser._games_by_gamekey[game].get_publisher())
    #         #print(parser._games_by_gamekey[game].get_year())
    #         #print(parser._games_by_gamekey[game].get_descr())
    #         #print(parser._games_by_gamekey[game].get_scoring())
    #         #print(parser._games_by_gamekey[game].get_tips())


# Process mame.xml file and get all the nessecary information
if __name__ == '__main__':

    # main loop to fetch all data
    parser = HistDatParser('history.dat')
    for game in title.keys():

        name = title[game]['title'].split('[')[0].split('(')[0].strip()
        status = title[game]['status']

        try:
            year = re.search('\d{4}', title[game]['year']).group(0)
        except:
            try:
                year = re.search('\d{4}', parser._games_by_gamekey['info_' + game].get_year().strip()).group(0)
            except:
                year = None

        manufacturer = title[game]['manufacturer']
        orientation = title[game]['rotate']
        cloneof = title[game]['cloneof']
        nrofbuttons = title[game]['nrofbuttons']
        controller = title[game]['controllers']

        if game in categories:
            genre = categories[game]
            if '*Mature*' in genre:
                genre = genre.replace(' *Mature*','')
                mature = 'Yes'
            else:
                mature = None
            if '/' in genre:
                genre = genre.split('/')[0].strip()
        else:
            genre = None
            mature = None

        try:
            description = parser._games_by_gamekey['info_' + game].get_descr().strip()
            if description == "":
                description = None
        except:
            description = None

        try:
            tips = parser._games_by_gamekey['info_' + game].get_tips().strip()
            if tips == "":
                tips = None
        except:
            tips = None

        try:
            scoring = parser._games_by_gamekey['info_' + game].get_scoring().strip()
            if scoring == "":
                scoring = None
        except:
            scoring = None

        try:
            player = players[game]
        except:
            player = title[game]['players']

        try:
            control = controls[game]
        except:
            control = None


        SQDB.execute('INSERT INTO mame (filename_rom, cloneof, name, description, tips, scoring, year, manufacturer, genre, status, orientation, players, mature, buttons, nrofbuttons, controller) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', [game, cloneof, name, description, tips, scoring, year, manufacturer, genre, status, orientation, player, mature, control, nrofbuttons, controller])

    SQDB.commit()

    # raise SystemExit(0)

