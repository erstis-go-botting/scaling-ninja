# coding=utf-8
__author__ = 'sudo'

from bs4 import BeautifulSoup
from json import loads
import re
from math import sqrt
from collections import OrderedDict



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
        self.filtered_map = self.remove_noobprot(self.raw_map)


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
                    village = sublist[x_modifier][y_modifier]
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
                                               'barb': barbarian, 'distance': distance}

        # sort for distance, bitchez!
        return OrderedDict( sorted( raw_map.items( ), key = lambda t: t[ 1 ][ 'distance' ] ) )

    @staticmethod
    def remove_noobprot(old_map):
        """
        Just removes protected elements
        """
        new_map = OrderedDict([ objekt for objekt in old_map.items( ) if objekt[ 1 ][ 'noobprot' ] == 0 ])
        return new_map

    @staticmethod
    def distance( home, target ):
        value = (int(home[ 'x' ]) - int(target[ 'x' ])) ** 2 + (int(home[ 'y' ]) - int(target[ 'y' ])) ** 2
        return sqrt( value )

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
            url = element.get('href')
            village_id = re.findall( r'id=(\d+)', url )[0]
            villages_under_attack.add(village_id)

        return villages_under_attack
