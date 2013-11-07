# coding=utf-8
__author__='sudo'

from json import loads
import re
import datetime
from math import sqrt
from collections import OrderedDict
from bs4 import BeautifulSoup
from tools import toolbox


class FarmTargetHandler(object):
    """
    A class for data handling related to farming
    """

    def __init__(self, bot):
        """
        Get that juicy data container class
        """

        self.temp_map=OrderedDict()

        self.bot=bot
        self.raw_map=self.analyze_map()
        self.under_attack=self.get_villages_under_attack()
        self.dangerous_items=self.parse_reports()

        # filter that map
        self.filtered_map=self.remove_noobprot(self.raw_map)
        self.filtered_map=self.remove_dangerous(self.filtered_map)
        self.filtered_map=self.remove_under_attack(self.filtered_map)

    def analyze_map(self, goto_x=None, goto_y=None, recursion_counter=0):

        """
        Analyzes the mapz
        and creates the raw_map dictionary with loads of entries. looks like this:
        {village_id: {'noobprot': 1, 'barb': 0, 'player_id': u'8891339', 'points': 79, 'y': 343, 'x': 704}}
        """

        x, y=self.bot.var_game_settings['village']['coord'].split('|')
        own_coordinates={'x': int(x), 'y': int(y)}

        if not goto_x and not goto_y:
            goto_x, goto_y=x, y

        goto='http://{self.bot.world}.die-staemme.de/game.php?x={goto_x}&y={goto_y}&screen=map#{goto_x};{goto_y}'.format(**locals())
        self.bot.browser.open(goto)
        htmllines=self.bot.browser.response().readlines()

        prefech=str()
        for line in htmllines:
            if 'TWMap.sectorPrefech' in line:
                prefech=line
                break

        if not prefech:
            print 'prefech not defined'
            raise

        prefech=loads(prefech.split(' = ', 1)[1][:-2])

        for superlist in prefech:
            base_x, base_y=superlist['data']['x'], superlist['data']['y']
            sublist=superlist['data']['villages']
            # some of those sublists are dictionaries, some of them are lists.
            # we need them to be of the same format for proper parsing
            temp_equal=dict()
            if type(sublist) is dict:
                temp_equal=sublist
            elif type(sublist) is list:
                for i, element in enumerate(sublist):
                    temp_equal[str(i)]=element
            else:
                print 'Unexpected type encountered in analyze_map'
                raise

            sublist=temp_equal
            del temp_equal

            for x_modifier in sublist:
                for y_modifier in sublist[x_modifier]:

                    try:
                        village=sublist[x_modifier][y_modifier]
                    except TypeError:
                        print x_modifier, y_modifier
                        continue
                        # village is in the form: [u'69473', 7, u'Kentucky', u'342', u'9641899', u'100']
                    # a barbarian village is: [u'68444', 4, 0, u'47', u'0', u'100']
                    # [0] = villageid, [1] = ?, [2] = village_name, [3] = village_points, [4] = player_id, [5] = ?

                    # accessing the account owner: superlist['data']['players'][player_id]
                    # which looks like: [u'K\xf6nig Grauer Wolf', u'67', u'839', 0]
                    # [0] = name, [1] = points, [2] = alliance_id, [3] = 0 if no noobprot, else string.

                    village_id=village[0]
                    village_name=village[2]
                    if not village_name:
                        village_name='barbarian village'

                    player_id=village[4]
                    village_x=int(x_modifier)+int(base_x)
                    village_y=int(y_modifier)+int(base_y)

                    if player_id=='0':
                        player_points=village[3]
                        noobprot=0
                        barbarian=1
                    else:
                        barbarian=0
                        try:
                            player_points=superlist['data']['players'][player_id][1]
                            noobprot=superlist['data']['players'][player_id][3]
                        except KeyError:
                            # verlassenes dorf
                            player_points=village[3]
                            noobprot=0

                    if noobprot:
                        # 1 is more usefull than a string, which we would need to parse for time
                        noobprot=1

                    if village_id in self.temp_map.keys():
                        # there seeme to be a lot of duplicates in this list, which is possibly a bug
                        # of DS. doesn't harm though, so we are just ignoring it.
                        pass

                    else:
                        player_points=player_points.replace('.', '')
                        distance=self.distance(own_coordinates, {'x': village_x, 'y': village_y})

                        # Don't include self :P
                        if distance==0.0:
                            self.own_village={'x': village_x, 'y': village_y, 'player_id': player_id,
                                              'points': int(player_points.replace('.', '')), 'noobprot': noobprot,
                                              'barb': barbarian, 'distance': distance, 'village_id': village_id,
                                              'village_name': village_name, 'village_points': int(village[3].replace('.', ''))}

                        self.temp_map[village_id]={'x': village_x, 'y': village_y, 'player_id': player_id,
                                                   'points': int(player_points.replace('.', '')), 'noobprot': noobprot,
                                                   'barb': barbarian, 'distance': distance,
                                                   'village_id': village_id, 'village_name': village_name}


        # balancing the map.
        # crazy stuff
        max_right=max({self.temp_map[element]['x']-own_coordinates['x'] for element in self.temp_map})
        max_left=min({self.temp_map[element]['x']-own_coordinates['x'] for element in self.temp_map})
        max_up=max({self.temp_map[element]['y']-own_coordinates['y'] for element in self.temp_map})
        max_down=min({self.temp_map[element]['y']-own_coordinates['y'] for element in self.temp_map})

        tester={max_right: 'max_right', max_left: 'max_left', max_up: 'max_up', max_down: 'max_down'}
        weakness=min(tester, key=abs)
        if abs(weakness)<50 and recursion_counter<2:
            if tester[weakness]=='max_left' or tester[weakness]=='max_right':
                self.analyze_map(own_coordinates['x']+2*weakness, own_coordinates['y'], recursion_counter=recursion_counter+1)
            else:
                self.analyze_map(own_coordinates['x'], own_coordinates['y']+2*weakness, recursion_counter=recursion_counter+1)


        #rm self
        self.temp_map=OrderedDict([objekt for objekt in self.temp_map.items() if objekt[1]['player_id']!=self.own_village['player_id']])

        # sort for distance
        return OrderedDict(sorted(self.temp_map.items(), key=lambda t: t[1]['distance']))

    def custom_map(self, points=False, distance=False, rm_noobprot=True, rm_dangerous=True, include_cleared=True,
                   prefer_dangerous=True, rm_under_attack=True, min_points=0):
        """
        Generates a fantastic custom map (cmap)
        Should be pretty self explanatory.
        (obviously) returns cmap
        """
        cmap=self.raw_map
        cleared=toolbox.init_shelve("cleared")

        if rm_noobprot:
            cmap=self.remove_noobprot(cmap)
        if rm_dangerous:
            cmap=self.remove_dangerous(cmap)
        if rm_under_attack:
            cmap=self.remove_under_attack(cmap)
        if distance:
            cmap=OrderedDict([objekt for objekt in cmap.items() if objekt[1]['distance']<=distance])

        if points:
            if include_cleared:
                cmap=OrderedDict([objekt for objekt in cmap.items() if objekt[1]['points']<points or str(objekt[0]) in cleared.keys()])
            else:
                cmap=OrderedDict([objekt for objekt in cmap.items() if objekt[1]['points']<points and str(objekt[0]) not in cleared.keys()])

        if min_points:
            if prefer_dangerous:
                cmap=OrderedDict([objekt for objekt in cmap.items() if objekt[1]['points']>min_points or objekt[0] in self.dangerous_items])

            else:
                cmap=OrderedDict([objekt for objekt in cmap.items() if objekt[1]['points']>min_points])

        #atlas = OrderedDict( [ objekt for objekt in atlas.items( ) if objekt[ 1 ][ 'points' ] < 75 and
        #                                                              objekt[ 1 ][ 'distance' ] < 15 ] )

        return cmap

    @staticmethod
    def remove_noobprot(old_map):
        """
        Just removes protected elements
        """
        new_map=OrderedDict([objekt for objekt in old_map.items() if objekt[1]['noobprot']==0])
        return new_map

    def remove_dangerous(self, old_map):
        """
        Just removes protected elements
        """
        new_map=OrderedDict([objekt for objekt in old_map.items() if objekt[0] not in self.dangerous_items])
        return new_map

    def remove_under_attack(self, old_map):
        """
        Just removes attacked villages
        """
        new_map=OrderedDict([objekt for objekt in old_map.items() if objekt[0] not in self.under_attack])
        return new_map

    @staticmethod
    def distance(home, target):
        value=(int(home['x'])-int(target['x']))**2+(int(home['y'])-int(target['y']))**2
        return sqrt(value)

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

        def add_to_report_storage(data):
            """
            Diese funktion stellt sicher,
            dass in report_storage immer die aktuellsten
            daten (und nur diese!) gespeichert sind
            """
            report_storage=toolbox.init_shelve('report_storage')

            # um diese dorfid geht es hier. id ist ein python keyword
            # und wird deswegen nicht verwendet
            v_id=data['village_id']

            # wenn es diese dorfid noch gar nicht gibt, ist der fall einfach...
            if v_id not in report_storage.keys():
                report_storage[v_id]=data
                report_storage.close()
                return

            # wenn es diese dorfid so schon gibt, müssen die zeiten verglichen werden, um
            # zu sehen welcher aktueller ist
            if data['time']>report_storage[v_id]['time']:
                report_storage[v_id]=data
                report_storage.close()
                return

        def get_dangerous_items():
            """
            Diese funktion gibt einfach alle items in report_storage zurück,
            die nicht "green" sind.
            """

            report_storage=toolbox.init_shelve('report_storage')
            # all reports who are not green
            dang={item: report_storage[item] for item in report_storage if report_storage[item]['color']!='green'}

            # sort out old reports
            # alles, was älter als eineinhalb tage ist, ist "alt"
            old=datetime.timedelta(days=1, hours=12)
            now=datetime.datetime.now()
            dang={item: dang[item] for item in dang if not now-dang[item]['time']>old}
            return dang

        # Navigating to attack reports & making soup!

        # DECLARATIONS
        cleared=toolbox.init_shelve('cleared')
        dangerous=""
        # END OF DECLARATIONS

        # GET SOUP
        self.bot.open("report&mode=attack")
        soup=BeautifulSoup(self.bot.browser.response().read())
        # END OF GET SOUP

        # PARSE TABLE
        # Getting the right table (erster und letzter eintrag entfernen).
        rl=soup.find('table', id='report_list').find_all('tr')[1:-1]

        # ITERATING OVER EVERY REPORT #
        for row in rl:
            # get color
            color=str(re.findall('/([a-z_]+?)\.png', row.img.get('src'))[0])

            # get village_id
            village_id=str(self.string_to_id(row.span.span.get_text(strip=True)))

            # get a time_string & convert it
            time=toolbox.parse_time(row.find_all('td')[-1].string)

            # get report id
            report_id=str(re.search(r'(\d+)', row.span.span.get("id")).group(0))

            # making a new dictionary
            data={'report_id': report_id, 'color': color, 'village_id': village_id, 'time': time}

            add_to_report_storage(data)
            # END OF ITERATION #

        dangerous=get_dangerous_items()

        for item in dangerous:
            if item in cleared.keys():
                cleared.pop(item)
                cleared.sync()
                print "deleted village: {item}.".format(**locals())

        # Don't ask why or how this works. Deep magic.
        #toolbox.print_cstring("Cleared villages: "+", ".join( map( str, cleared.keys()))+". Anzahl: "+str(len(cleared)), 'yellow')

        return dangerous
        #print 'Village found with: {color}, {loot_status} ({x}|{y}) id = [{id_}]'.format(**locals())


    def string_to_id(self, inputstring):
        """
        Input a string (like: main.py (main.py) greift Bonusdorf (636|504) )
        and you get a village_id back. awesome.
        """

        coordinate_helper=re.search(r'(\d+)[|](\d+)', inputstring)
        x=coordinate_helper.group(1)
        y=coordinate_helper.group(2)
        id_=self.conversion_coord_to_id(x=x, y=y)

        return id_

    def conversion_coord_to_id(self, x, y):
        """
        expects 2 coordinates, returns an id
        (if the coordinates are stored in raw_map,
        else 0 is returned.)
        """
        x, y=int(x), int(y)

        try:
            id_=[element for element in self.raw_map if self.raw_map[element]['x']==x if self.raw_map[element]['y']==y][0]
        except IndexError:
            id_=0

        return id_

    def get_villages_under_attack(self):
        """
        A simple function which just returns
        a set containing village_ids, which are beeing attacked
        by the bot at the moment of the function call.

        Obtains results from:
        http://de99.die-staemme.de/game.php?village=17882&mode=commands&screen=overview_villages&type=attack

        if the farmgroup was sent to the destination more than a hour ago, it will not be marked as under attack!
        """

        villages_under_attack=set()
        self.bot.open('overview_villages&mode=commands&type=attack&group=0&page=-1')
        soup=self.bot.browser.response().read()
        soup=BeautifulSoup(soup)

        reg=re.compile(r'.*info_command')
        length=len(soup.find_all(href=reg))

        if int(length)>900:
            print "Hallo. Ich bin zu debugging zwecken hier. Eventuell funktioniert die Funktion"
            print "'get_villages_under_attack' nicht, für eine grosse Anzahl Angriffe (mehr als 1000)"
            print "Bitte ab und an manuell checken ob dieser wert stimmt: Anzahl Angriffe: {length}".format(length=length)
            print "(Wenn gewisse Dörfer mehrmals angegriffen werden, stimmt dieser Wert nicht.)"

        elements=soup.find_all("tr", class_=re.compile('nowrap.*'))

        for element in elements:
            tempcord=re.search(r'(\d+)[|](\d+)', element.span.span.get_text(strip=True))
            if not tempcord:
                continue
                # Dies passiert, wenn angriffe manuell umbenannt werden zB von "Angriff auf Barbarendorf (627|498) K46  Umbenennen"
                # zu "adelsgeschlecht, yay"

            id_=self.conversion_coord_to_id(x=tempcord.group(1), y=tempcord.group(2))

            tempcordown=re.search(r'(\d+)[|](\d+)', element.find_all("a", href=re.compile(r".*info_village"))[0].get_text(strip=True))
            distance=toolbox.calculate_distance(tempcordown.group(1), tempcordown.group(2), tempcord.group(1), tempcord.group(2))

            # lkavs have a speed of 10 minutes / tile. lkavs are the only relevant unit here.
            walktime=datetime.timedelta(minutes=distance*10)
            arrival=toolbox.parse_time(element.find_all("td")[2].get_text(strip=True))
            senttime=arrival-walktime

            if datetime.datetime.today()-senttime<datetime.timedelta(hours=1):
                villages_under_attack.add(id_)

        return villages_under_attack


