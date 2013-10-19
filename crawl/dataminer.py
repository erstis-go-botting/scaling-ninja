# coding=utf-8
__author__ = 'sudo'

from bs4 import BeautifulSoup
from json import loads
import re
from math import sqrt
from collections import OrderedDict
import datetime
from tools import toolbox


class FarmTargetHandler(object):
    """
    A class for data handling related to farming
    """
    def __init__(self, bot):
        """
        Get that juicy data container class
        """

        self.bot = bot
        self.raw_map = self.analyze_map()

        # filter that map
        self.filtered_map = self.remove_noobprot(self.raw_map)
        self.filtered_map = self.remove_dangerous(self.filtered_map)
        self.filtered_map = self.remove_under_attack(self.filtered_map)

    def analyze_map(self):

        """
        Analyzes the mapz
        and creates the raw_map dictionary with loads of entries. looks like this:
        {village_id: {'noobprot': 1, 'barb': 0, 'player_id': u'8891339', 'points': 79, 'y': 343, 'x': 704}}
        """

        x, y = self.bot.var_game_settings['village']['coord'].split('|')
        own_coordinates = {'x': x, 'y': y}

        goto = 'http://{self.bot.world}.die-staemme.de/game.php?x={x}&y={y}&screen=map#{x};{y}'.format(**locals())
        self.bot.browser.open(goto)
        htmllines = self.bot.browser.response().readlines()

        prefech = str()
        for line in htmllines:
            if 'TWMap.sectorPrefech' in line:
                prefech = line
                break

        if not prefech:
            print 'prefech not defined'
            raise

        prefech = loads(prefech.split(' = ', 1)[1][:-2])
        raw_map = OrderedDict()

        for superlist in prefech:
            base_x, base_y = superlist['data']['x'], superlist['data']['y']

            sublist = superlist['data']['villages']
            # some of those sublists are dictionaries, some of them are lists.
            # we need them to be of the same format for proper parsing
            temp_equal = dict()
            if type(sublist) is dict:
                temp_equal = sublist
            elif type(sublist) is list:
                for i, element in enumerate(sublist):
                    temp_equal[str(i)] = element
            else:
                print 'Unexpected type encountered in analyze_map'
                raise

            sublist = temp_equal
            del temp_equal

            for x_modifier in sublist:
                for y_modifier in sublist[x_modifier]:

                    try:
                        village = sublist[x_modifier][y_modifier]
                    except TypeError:
                        print x_modifier, y_modifier
                        continue
                    # village is in the form: [u'69473', 7, u'Kentucky', u'342', u'9641899', u'100']
                    # a barbarian village is: [u'68444', 4, 0, u'47', u'0', u'100']
                    # [0] = villageid, [1] = ?, [2] = village_name, [3] = village_points, [4] = player_id, [5] = ?

                    # accessing the account owner: superlist['data']['players'][player_id]
                    # which looks like: [u'K\xf6nig Grauer Wolf', u'67', u'839', 0]
                    # [0] = name, [1] = points, [2] = alliance_id, [3] = 0 if no noobprot, else string.

                    village_id = village[0]
                    player_id = village[4]
                    village_x = int(x_modifier) + int(base_x)
                    village_y = int(y_modifier) + int(base_y)

                    if player_id == '0':
                        player_points = village[3]
                        noobprot = 0
                        barbarian = 1
                    else:
                        barbarian = 0
                        try:
                            player_points = superlist['data']['players'][player_id][1]
                            noobprot = superlist[ 'data' ][ 'players' ][ player_id ][ 3 ]
                        except KeyError:
                            # verlassenes dorf
                            player_points = village[ 3 ]
                            noobprot = 0

                    if noobprot:
                        # 1 is more usefull than a string, which we would need to parse for time
                        noobprot = 1

                    if village_id in raw_map.keys():
                        # there seeme to be a lot of duplicates in this list, which is possibly a bug
                        # of DS. doesn't harm though, so we are just ignoring it.
                        pass
                    else:
                        player_points = player_points.replace( '.', '' )
                        distance = self.distance(own_coordinates, {'x': village_x, 'y': village_y})
                        # Don't include self :P
                        if distance == 0.0:
                            continue

                        raw_map[village_id] = {'x': village_x, 'y': village_y, 'player_id': player_id,
                                               'points': int( player_points.replace('.', '') ), 'noobprot': noobprot,
                                               'barb': barbarian, 'distance': distance, 'village_id': village_id}

        # sort for distance
        return OrderedDict( sorted( raw_map.items( ), key = lambda t: t[ 1 ][ 'distance' ] ) )

    def custom_map(self, points = False, distance = False, rm_noobprot = True, rm_dangerous = True, include_cleared = True,
                   prefer_dangerous = True, rm_under_attack = True, only_barbarians = False, min_points = 0):
        """
        Generates a fantastic custom map (cmap)
        Should be pretty self explanatory.
        (obviously) returns cmap
        """
        cmap = self.raw_map
        cleared = toolbox.init_shelve( "cleared" )

        if rm_noobprot:
            cmap = self.remove_noobprot(cmap)
        if rm_dangerous:
            cmap = self.remove_dangerous(cmap)
        if rm_under_attack:
            cmap = self.remove_under_attack(cmap)
        if distance:
            cmap = OrderedDict( [ objekt for objekt in cmap.items() if objekt[1]['distance'] < distance])
        if points:
            if include_cleared:
                cmap = OrderedDict( [ objekt for objekt in cmap.items( ) if objekt[ 1 ][ 'points' ] < points or str(objekt[0]) in cleared.keys()] )
            else:
                cmap = OrderedDict( [ objekt for objekt in cmap.items( ) if objekt[ 1 ][ 'points'  < points] and str(objekt[0]) not in cleared.keys()] )

        if min_points:
            if prefer_dangerous:
                dangerous_items = self.parse_reports( ).items( )
                cmap = OrderedDict( [ objekt for objekt in cmap.items( ) if objekt[ 1 ][ 'points' ] > min_points  and objekt[0] not in dangerous_items ])

            else:
                cmap = OrderedDict( [ objekt for objekt in cmap.items( ) if objekt[ 1 ][ 'points' ] > min_points ])
        if only_barbarians:
            print 'only_barbarians not implemented yet'
            pass

        #atlas = OrderedDict( [ objekt for objekt in atlas.items( ) if objekt[ 1 ][ 'points' ] < 75 and
        #                                                              objekt[ 1 ][ 'distance' ] < 15 ] )

        return cmap

    @staticmethod
    def remove_noobprot(old_map):
        """
        Just removes protected elements
        """
        new_map = OrderedDict([ objekt for objekt in old_map.items( ) if objekt[ 1 ][ 'noobprot' ] == 0 ])
        return new_map

    def remove_dangerous(self, old_map):
        """
        Just removes protected elements
        """
        dangerous_items = self.parse_reports().items()
        new_map = OrderedDict([ objekt for objekt in old_map.items() if objekt[0] not in dangerous_items ])
        return new_map

    def remove_under_attack( self, old_map ):
        """
        Just removes attacked villages
        """
        under_attack = self.get_villages_under_attack()
        new_map = OrderedDict( [ objekt for objekt in old_map.items( ) if objekt[ 0 ] not in under_attack ] )
        return new_map

    @staticmethod
    def distance( home, target ):
        value = (int(home[ 'x' ]) - int(target[ 'x' ])) ** 2 + (int(home[ 'y' ]) - int(target[ 'y' ])) ** 2
        return sqrt( value )

    def parse_reports(self):
        """
        Reads the reports and stuff
        """
        def deepscan(data_container):
            """
            Opens reports and scans them for fun & profit
            """

            for object in data_container:
                # open the report & make soup

                pass

                #self.bot.open("report&mode=all&view=%s" % object['report_id'])
                #soup = BeautifulSoup(self.bot.browser.response().read())
                #loot = soup.find( "table", id = "attack_results" ).td.next_sibling.next_sibling.string
                #got, max = re.findall('\d+', loot)
                #

        # Navigating to attack reports & making soup!

        # DECLARATIONS
        dangerous = toolbox.init_shelve( 'reports_storage' )
        report_id_to_deepscan = list()
        cleared = toolbox.init_shelve( "cleared" )
        # END OF DECLARATIONS

        # GET SOUP
        self.bot.open("report&mode=attack")
        soup = BeautifulSoup(self.bot.browser.response().read())
        # END OF GET SOUP

        # PARSE TABLE
        # Getting the right table (erster und letzter eintrag entfernen.
        rl = soup.find( 'table', id = 'report_list' ).find_all('tr')[1:-1]

        for row in rl:

            # get color
            color = re.findall( '/([a-z]+?)\.png', row.img.get('src') )[0]

            # get village_id
            village_id = self.string_to_id(row.span.span.get_text( strip = True ))

            # get a time_string & convert it
            time = toolbox.parse_time(row.find_all('td')[-1].string)

            # get report id
            report_id = re.search(r'(\d+)', row.span.span.get("id")).group(0)

            # we deepscan everything that is either not in our database, or that we have a
            # newer report of.
            if village_id not in dangerous.keys() or time > dangerous[str(village_id)]['time']:
                if color != 'green':

                    data = {'report_id': report_id, 'color': color, 'village_id': village_id, 'time':time}
                    print data
                    dangerous[str(village_id)] = data


            if village_id in cleared.keys() and color != 'green':
                cleared.pop( str( village_id ) )
                cleared.sync( )
                print "deleted village: {village_id} from cleared.".format( **locals( ) )

        print cleared
        dangerous.sync()
        return dangerous
            #print 'Village found with: {color}, {loot_status} ({x}|{y}) id = [{id_}]'.format(**locals())


    def string_to_id(self, inputstring):
        """
        Input a string (like: main.py (main.py) greift Bonusdorf (636|504) )
        and you get a village_id back. awesome.
        """

        coordinate_helper = re.search( r'(\d+)[|](\d+)', inputstring )
        x = coordinate_helper.group( 1 )
        y = coordinate_helper.group( 2 )
        id_ = self.conversion_coord_to_id( x = x, y = y )

        return id_


    def conversion_coord_to_id(self, x, y):
        """
        expects 2 coordinates, returns an id
        (if the coordinates are stored in raw_map,
        else 0 is returned.)
        """
        x, y = int(x), int(y)

        try:
            id_ = [element for element in self.raw_map if self.raw_map[element]['x'] == x if self.raw_map[element]['y'] == y][0]
        except IndexError:
            id_ = 0

        return id_

    def get_villages_under_attack(self):
        """
        A simple function which just returns
        a set containing village_ids, which are beeing attacked
        by the bot at the moment of the function call.

        Obtains results from:
        http://de99.die-staemme.de/game.php?village=17882&mode=commands&screen=overview_villages&type=attack
        """
        villages_under_attack = set()

        self.bot.open('overview_villages&type=attack&mode=commands')
        soup = self.bot.browser.response().read()
        soup = BeautifulSoup(soup)
        reg = re.compile( r'.*info_command' )

        for element in soup.find_all(href = reg):
            coordinate_helper = re.search( r'(\d+)[|](\d+)', element.get_text(strip = True) )

            x = coordinate_helper.group(1)
            y = coordinate_helper.group(2)

            id_ = self.conversion_coord_to_id( x = x, y = y )

            villages_under_attack.add(id_)

        return villages_under_attack

    def owned_villages(self):
        """
        Gets a list with the ID's of every owned village.
        """

        own_villages = set()

