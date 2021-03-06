# coding=utf-8
__author__ = 'sudo'

import re

from json import loads
from bs4 import BeautifulSoup
from ConfigParser import ConfigParser
from tools import toolbox


import cPickle as pickle


class BotContainer(object):
    """
    The BotContainer class is awesome.
    """
    def __init__(self, br):
        """
        Sets up basic attributes, which we will heavily rely on.
        All settings are loaded from settings\settings.ini
        """



        if not toolbox.is_logged_in( br ):
            toolbox.login( br )


        self.config = ConfigParser()
        self.config.read(r'settings\settings.ini')

        # fetch the credentials.
        self.world = self.config.get('credentials', 'world')
        self.username = self.config.get('credentials', 'username')
        self.password = self.config.get('credentials', 'password')

        # initiate the browser.
        # This is kinda ugly, but there is afaik no other way
        # to keep the browser object alive other than storing it in
        # the outer {while True} loop.
        self.browser = br

        # Initialize the statistics object
        try:
            self.statistics = pickle.load(open('juicy_stats', 'rb'))
        except IOError:
            # If there are no statistics as of right now we are gonna create them.
            self.statistics = {'units_built': {'axe': 0, 'sword': 0, 'archer': 0, 'spear': 0, 'light': 0,'heavy': 0,
                                               'marcher': 0, 'spy': 0, 'ram': 0, 'catapult': 0},
                               'buildings_constructed': 0, 'trades_conducted': 0}

        # dummy initialize the attributes
        self.ressources = dict()
        self.units = dict()
        self.buildings = dict()
        self.buildable = list()
        self.worldsettings = dict()
        self.var_game_settings = dict()
        self.next_building = str()
        self.parse_worldsettings()
        self.pop_critical, self.storage_critical = 0, 0

        # Fetch all data from die-stämme (ressources, units usw...)
        self.refresh_all()

    def parse_worldsettings(self):
        """
        Parses and fetsches some attributes from /stat.php?mode=settings
        ! to fetch the settings no login is required !
        """

        self.browser.open('http://{world}.die-staemme.de/stat.php?mode=settings'.format(world=self.world))
        soup = BeautifulSoup(self.browser.response().read())

        # get raw text
        raw_text = soup.get_text('\n', True).split('\n')
        keywords = ['Kirche', u'Bogenschützen', 'Paladin', 'Miliz']

        # The line after a keyword gets mapped against the keyword in question
        for i in range(0, len(raw_text)):
            for keyword in keywords:
                if keyword == raw_text[i]:
                    # Unicode workaround...
                    if keyword == u'Bogenschützen':
                        keyword = 'Archer'
                    # setting the value to a somewhat more useful format
                    if raw_text[i+1] == 'aktiv':
                        value = 1
                    elif raw_text[i+1] == 'inaktiv':
                        value = 0
                    else:
                        value = 'parsing failure'
                    self.worldsettings[unicode(keyword)] = value

    def open(self, place, data=None, village=None):
        """
        opens an url and tests for botprotection
        """
        if not village:
            self.browser.open('http://{self.world}.die-staemme.de/game.php?screen={place}'.format(**locals()), data)
        else:
            self.browser.open('http://{self.world}.die-staemme.de/game.php?screen={place}&village={village}'.format(**locals()), data)

        if 'Botschutz' in self.browser.response().read():
            toolbox.print_cstring('Botprotection strikes again. Trying to fix it.', 'magenta')
            self.handle_botprotection(self, origin=place)


    @staticmethod
    def handle_botprotection(self, origin=None):
        """
        This function handles the evil botprotection.
        It even accepts an origin parameter to go back to whatever operation was in progress.
        Tries to open the origin url after completion and gives the control back to the calling function.
        """

        # TODO write this little function perhaps. Remove @staticmethod perhaps. be imba perhaps.

        toolbox.botprot(self.browser)

    def refresh_all(self):
        """
        Refreshes the attributes of the botobject
        Currently refreshes:
        self.ressources
        self.units
        self.var_game_data
        self.buildings
        """
        self.get_ressources()
        self.get_units()
        self.get_var_game_data()
        self.get_buildings()
        self.get_next_building()

        for element in ['stone', 'wood', 'iron']:
            if self.ressources[element]>self.ressources['storage']*0.6:
                self.storage_critical=1
                break
            else:
                self.storage_critical=0

        if self.ressources['pop_now']>self.ressources['pop_max']*0.8:
            self.pop_critical=1
        else:
            self.pop_critical=0

    def get_next_building(self):
        """
        Extracts data from 'settings\buildings.txt'
        and sets the variable next_building.
        """
        fileo = open( r'settings\buildings.txt', 'r' ).readlines( )
        for line in fileo:
            line = line.strip().split()
            if line:
                building, lvl = line[0], int(line[1])
                if self.buildings[building] < lvl:
                    self.next_building = building
                    return
        self.next_building = ''

    def get_ressources(self):
        """
        Returns all ressources
        And saves them in bot.ressources (dict format)
        """
        self.open('overview')
        soup = BeautifulSoup(self.browser.response().read())

        # get all those neat values
        storage = soup.find(id='storage').string
        wood = soup.find(id='wood').string
        stone = soup.find(id='stone').string
        iron = soup.find(id='iron').string
        pop_now = soup.find(id='pop_current_label').string
        pop_max = soup.find(id='pop_max_label').string
        ressources = {'iron': iron, 'stone': stone, 'wood': wood,
                      'storage': storage, 'pop_now': pop_now, 'pop_max': pop_max}

        # make everything int!
        self.ressources = {element: int(ressources[element]) for element in ressources}

    def get_units(self):
        """
        Returns all the units!
        And saves them in bot.units (dict format)
        """

        # TODO ADD PALADIN SUPPORT
        # TODO ADD GARAGE / STABLE

        units = dict()

        def parse_units(give_me_soup, unit_list, building ):

            rows = give_me_soup.find_all(class_='row_a')
            for i, element in enumerate( unit_list ):
                try:
                    temp = rows[ i ].find_all( 'td' )[ -2 ].string.split( r'/' )
                    units[ element ] = { 'available': int( temp[ 0 ] ), 'all': int( temp[ 1 ] ) }
                except IndexError:
                    units[ element ] = { 'available': 0, 'all': 0 }

            try:
                # Gets units which are beeing built atm and the queue time.
                current_queue = give_me_soup.find( 'div', class_ = 'trainqueue_wrap' ).find_all( 'tr' )
                if len( current_queue ) == 2:
                    current_queue = [ current_queue[ 1 ] ]
                else:
                    current_queue = current_queue[ 1:-1 ]

                for element in current_queue:
                    art = re.findall( r'smaller (.+)">', str( element.div ) )[ 0 ]
                    count = element.td.contents[ -1 ].strip( ).split( )[ 0 ]

                    try:
                        timelist = map( int, element.span.string.split( ':' ) )
                    except AttributeError:
                        timelist = map( int, re.findall( r'\d+', str( element ) )[ 2:5 ] )
                    time = 60 * 60 * timelist[ 0 ] + 60 * timelist[ 1 ] + timelist[ 2 ]
                    # this is false!
                    #units[ art ][ 'available' ] += int( count )
                    units[ '{b}_time'.format(b=building) ] += int( time )


            except AttributeError:
                units[ '{b}_time'.format(b=building) ] += 0

        def barracks():
            """
            Fetches all barracks units
            """
            b_units = ['spear', 'sword', 'axe', 'archer']
            self.open('barracks')
            soup = BeautifulSoup(self.browser.response().read())

            if 'nicht vorhanden' in str(soup):
                for element in b_units:
                    units[element] = {'available': 0, 'all': 0}

            # Soup von der ganzen Seite -> Alle Reihen finden -> zweitletzte Spalte finden
            # diese Werte dort drin jeweils einer Einheit zuordnen.
            units['barracks_time'] = 0
            parse_units(soup, b_units, 'barracks')

        def stable():
            """
            Fetches all stable units
            """
            s_units = ['spy', 'light', 'marcher', 'heavy']
            self.open('stable')
            soup = BeautifulSoup(self.browser.response().read())

            if 'nicht vorhanden' in str(soup):
                for element in s_units:
                    units[element] = {'available': 0, 'all': 0}

            # Soup von der ganzen Seite -> Alle Reihen finden -> zweitletzte Spalte finden
            # diese Werte dort drin jeweils einer Einheit zuordnen.
            rows = soup.find_all(class_='row_a')
            for i, element in enumerate(s_units):
                try:
                    temp = rows[i].find_all('td')[-2].string.split(r'/')
                    units[element] = {'available': int(temp[0]), 'all': int(temp[1])}
                except IndexError:
                    units[element] = 'None'

            units['stable_time'] = 0
            parse_units(soup, s_units, 'stable')

        def garage():
            """
            Fetches all garage units
            """
            # TODO this is just a dummy version
            garage_units = ['ram', 'catapult']
            self.open('garage')
            soup = BeautifulSoup(self.browser.response().read())

            if 'nicht vorhanden' in str(soup):
                for element in garage_units:
                    units[element] = 'None'

            # Soup von der ganzen Seite -> Alle Reihen finden -> zweitletzte Spalte finden
            # diese Werte dort drin jeweils einer Einheit zuordnen.
            rows = soup.find_all(class_='row_a')
            for i, element in enumerate(garage_units):
                try:
                    temp = rows[i].find_all('td')[-2].string.split(r'/')
                    units[element] = {'available': int(temp[0]), 'all': int(temp[1])}
                except IndexError:
                    units[element] = 'None'

            units['garage_time'] = 0
            parse_units(soup, garage_units, 'garage')
            
        def quest_workaround():
            """
            This is a function to get those 10 axis / 10 swordies
            you get with quests (without having the means to build them)
            --> the other functions fail to fetch them.
            """
            self.open('overview')
            soup = self.browser.response().read()
            soup = BeautifulSoup(soup)

            for fragment in soup.get_text().split('\n'):
                if u'Schwertkämpfer' in fragment:
                    helper = int(fragment.split(' ')[0])
                    if helper > units['sword']['available']:
                        units['sword']['available'] = helper

                elif u'Axtkämpfer' in fragment:
                    helper = int(fragment.split(' ')[0])
                    if helper > units['axe']['available']:
                        units['axe']['available'] = helper

        barracks()
        stable()
        garage()
        quest_workaround()


        self.units = units

    def get_buildings(self):
        """
        get's sexy schmexy buildings.
        also adds a variable 'under_construction' to the dictionary.
        and adds buildings which are currently beeing constructed.

        additionally botcontainer.buildable is set
        """

        if not self.var_game_settings:
            print 'I need those var_game_settings'
            raise

        buildings = self.var_game_settings['village']['buildings']
        buildings = {key: int(buildings[key]) for key in buildings}

        self.open('main')
        html = self.browser.response().read()
        soup = BeautifulSoup( html )

        # add buildables
        list_buildable = soup.find_all( 'a', id = re.compile( r'main_buildlink_(.*)' ) )
        for element in list_buildable:
            self.buildable.append(re.findall( r'main_buildlink_(.*?)"', str( element ) )[ 0 ])
        # end of add buildables


        #check if there is something currently beeing built
        if 'buildorder_' not in html:
            self.buildings = buildings
            buildings[ 'under_construction' ] = 0
            return

        temp_under_construction = soup.find( 'tbody', id = 'buildqueue' ).find_all( class_ = re.compile( 'buildorder_.+' ) )

        buildings['under_construction'] = len(temp_under_construction)

        for item in temp_under_construction:
            typ = re.findall('buildorder_(.+?)"', str(item))[0]
            buildings[typ] = int(buildings[typ]) + 1

        self.buildings = buildings

    def get_var_game_data(self, locale=False):
        """
        get's sexy schmexy var_game_data
        """
        if not locale:
            self.open('overview')

        htmllines = self.browser.response().readlines()
        vg = None

        for line in htmllines:
            if 'var game_data' in line:
                # vg is a json object
                vg = line.split('=', 1)[1].strip()[:-1]
                break

        try:
            self.var_game_settings = loads(vg)
        except TypeError:
            print 'dataminer.var_game_data got no json object. this shouldn\'t happen'
            raise TypeError

    def close(self):
        # save our statistics
        pickle.dump(self.statistics, open('juicy_stats', 'wb'))

    def get_village_ids(self):
        """"
        just returns a set cointaining all village ids
        """

        self.open("overview_villages&mode=groups")
        soup=BeautifulSoup(self.browser.response().read())
        linklist=[element for element in soup.find_all("a") if element.get("href") if
                  re.search(r'(\d+)&amp;screen=overview">', str(element))]
        ids={re.search(r'(\d+)', e.get("href")).group(0): e.span.string for e in linklist}
        return ids