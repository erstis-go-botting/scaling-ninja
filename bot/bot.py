# coding=utf-8
__author__ = 'sudo'

import re
from bs4 import BeautifulSoup
from mechanize._mechanize import LinkNotFoundError
from tools.toolbox import print_cstring
from crawl.botContainer import BotContainer
from crawl.dataminer import FarmTargetHandler
import mechanize
import datetime
from itertools import cycle
import tools.toolbox
from collections import OrderedDict

# UNITTRAIN BARRACKS
# url [h = actioncode]
# village=1979&ajaxaction=train&h=7852&mode=train&screen=barracks
# form data
# units%5Bspear%5D=2

# ATTACK


class Bot(BotContainer):
    """
    Just a bot, to pwn the world.
    Inherits from crawl.BotContainer -> so everything in crawl.BotContainer
    is available here as well. awesome.

    what should be done with each loop (in this order):

    - look if there are incomings

    Decide (based on cost/ available ressources/ available storage):
    - trade!
    - construct new buildings
    - train new units

    - farm
    """
    def __init__(self, br):
        BotContainer.__init__(self, br=br)

        # is the storage very full?
        for element in ['stone', 'wood', 'iron']:
            if self.ressources[element] > self.ressources['storage'] * 0.85:
                self.storage_critical = 1
                break
            else:
                self.storage_critical = 0
        #
        self.fth = FarmTargetHandler( self )

        # is the farm very full?
        if self.ressources['pop_now'] > self.ressources['pop_max'] * 0.8:
            self.pop_critical = 1
        else:
            self.pop_critical = 0

    def construct(self):

        """
        access various information to determines if something
        should be constructed. and constructs it, if necessary.
        """
        if self.buildings['under_construction']:
            return

        def build(building):
            """
            constructs building
            """
            self.open('main')

            try:
                self.browser.follow_link(self.browser.find_link(url_regex=
                re.compile("upgrade_building.+id=%s" % building)))
                print_cstring("Building: [%s]" % building, 'turq')
                self.statistics['buildings_constructed'] += 1
            except LinkNotFoundError:
                print_cstring( 'fuck that shit, not enough ressources to build [%s]' % building, 'red')

        # making sure to build storage & farm only when needed.
        self.open('main')
        html = self.browser.response().read()
        farm_building = '\t\t\tBauernhof<br />\n\t\t\tStufe' in html
        storage_building = '\t\t\tSpeicher<br />\n\t\t\tStufe' in html

        if self.pop_critical and 'farm' in self.buildable and not farm_building:
            build( 'farm' )
        elif self.storage_critical and 'storage' in self.buildable and not storage_building:
            build('storage')
        elif self.next_building in self.buildable:
            build(self.next_building)

    def trade(self):
        """
        implementing basic trading...
        """

        def do_trade(buy_item, sell_item, trader_count, sell_count=1000, buy_count=999, max_time = 2):
            """
            the function that actually does the trade
            """
            self.open('market&mode=own_offer')
            if int(sell_count) > 1000 or int(buy_count) > 1000:
                print 'incorrect function usage. a trader can only carry 1k ressources'

            self.browser.select_form( nr = 0 )
            self.browser.form[ "sell" ] = str(sell_count)
            self.browser.form[ "buy" ] = str(buy_count)
            self.browser.form[ "res_sell" ] = [ str( sell_item ) ]
            self.browser.form[ "res_buy" ] = [ str( buy_item ) ]
            self.browser.form[ "max_time" ] = str( max_time )
            self.browser.form[ "multi" ] = str( trader_count )
            self.browser.submit( )
            self.statistics['trades_conducted'] += trader_count

        self.open('market&mode=send')
        html = self.browser.response( ).readlines( )

        #region get trader
        # get trader ----------------------------------------- #
        curtrader, maxtrader = 0, 0
        for line in html:
            if re.compile( r"ndler: [0-9]+[/][0-9]+" ).search( line ):
                curtrader, maxtrader, = map(int, re.compile( r"[0-9]+" ).findall( line )[ :2 ])


        # no point in trading if we haven't got any traders...
        if not curtrader:
            return

        # create a clon of ressources to modify it to our (temporary needs)
        trading_ressources = self.ressources.copy()

        # end of get trader ---------------------------------- #
        #endregion

        # ---------------------------------------------------- ]

        #region get incoming ressources

        # Get incoming ressources ---------------------------- #
        helper = 0
        for line in html:
            line = line.replace( '<span class="grey">.</span>', '' )

            if helper == 2:


                try:
                    ressources_incoming = int( re.compile( r'\d+' ).findall( line )[ 0 ] )
                    if 'iron' in line:
                        trading_ressources['iron'] += ressources_incoming
                    elif 'stone' in line:
                        trading_ressources['stone'] += ressources_incoming
                    elif 'wood' in line:
                        trading_ressources['wood'] += ressources_incoming
                    else:
                        print 'error: ', line

                except IndexError:
                    print 'inc'

                helper -= 1

            if 'Lieferung von' in line:
                helper = 2
        # End of get incoming ressources --------------------- #
        #endregion

        # ---------------------------------------------------- ]

        #region selber angebotene ressourcen

        # Ressourcen, die selber angeboten sind auslesen ----- #
        # TODO CANCEL STUFF YOU DON'T WANT TO OFFER ANYMORE
        self.open('market&mode=own_offer')
        soup = BeautifulSoup(self.browser.response().read())

        # relevant_tables beinhaltet Zeilen mit unseren Angeboten.
        try:
            relevant_tables = soup.find("table", id="own_offers_table").find_all("tr")[1:-1]
        except AttributeError:
            relevant_tables = []

        request_type, request_amount = 0, 0
        for table in relevant_tables:
            offer = table.find_all("td")[1]
            request = table.find_all("td")[2]

            offer_type = offer.span['class'][2]
            request_type = request.span['class'][2]

            offer_amount = re.findall(r'\d+', str(offer).replace('<span class="grey">.</span>', ''))[0]
            request_amount = re.findall(r'\d+', str(request).replace('<span class="grey">.</span>', ''))[0]

            trading_ressources[request_type] += int(request_amount)
        # EOF Ressourcen die selber angeboten werden auslesen  #
        #endregion

        # ---------------------------------------------------- ]

        #region determine what to trade

        # Determine what we want to trade bitchezzzz! -------- #
        average = ( trading_ressources['stone'] + trading_ressources['wood'] + trading_ressources['iron'] ) / 3
        keys = ['stone', 'wood', 'iron']
        requ, offer = dict(), dict()

        for key in keys:
            difference = average - trading_ressources[key]

            if abs(difference) < 1000:
                continue
            elif difference <= -1000:
                difference = abs(difference/1000)
                offer[key] = difference
            elif difference >= 1000:
                difference =  difference / 1000
                requ[key] = difference
            else:
                print 'error in trading func'
        # EOF Determine what we want to trade ---------------- #
        #endregion

        # ---------------------------------------------------- ]


        # bei einer guten balance muessen wir nicht traden
        if not requ or not offer:
            return

        want_to_trade = sum(requ.values())
        buy, sell, count = 0, 0, 0

        #region LOGIC! COOL STUFF!
        # CASE 1: We have 2 requests and not enough traders to satisfy our demands.
        # --> we just trade as much as possible for the type that needs the most.
        if len(requ) == 2 and curtrader < want_to_trade:
            req_art = max( requ, key = requ.get )
            req_demand = requ[req_art]
            req_count = req_demand if req_demand < curtrader else curtrader

            offer_art = offer.keys()[0]

            buy, sell, count = req_art, offer_art, req_count


        # CASE 2: We have 2 requests and enough traders to satisfy our demands.
        elif len(requ) == 2:
            offer_art = offer.keys()[0]
            for element in requ:
                req_art = element
                req_demand = requ[req_art]

                buy, sell, count = req_art, offer_art, req_demand


        # CASE 3: We have 2 offers and not enough traders to satisfy our demands.
        # --> We just give as much as possible from the ressource we have the most of. imba.
        elif len(offer) == 2 and curtrader < want_to_trade:
            req_art = requ.keys()[0]

            offer_art = max( offer, key = offer.get )
            offer_support = offer[offer_art]
            offer_count = offer_support if offer_support < curtrader else curtrader

            buy, sell, count = req_art, offer_art, offer_count


        # Case 4: We have 2 offers and enough traders to satisfy our demands.
        elif len(offer) == 2:
            req_art = requ.keys( )[ 0 ]
            for element in offer:
                offer_art = element
                offer_support = offer[offer_art]

                buy, sell, count = req_art, offer_art, offer_support

        # Case 4: We have 1 offer and 1 request.
        elif len(offer) == 1 and len(requ) == 1:
            req_art = requ.keys()[0]
            offer_art = offer.keys()[0]

            count = requ[req_art] if requ[req_art] < curtrader else curtrader

            buy, sell, count = req_art, offer_art, count

        else:
            print 'Something was very strange in trade func'
            raise
        #endregion

        do_trade(buy, sell, count, max_time=2)

        print_cstring('Buying {buy} for {sell} {count} times.'.format(buy=buy, sell = sell, count = count),'turq')

    def recruit(self):
        """
        A function to recruit units
        Units werden rekrutiert, wenn:

        - Ein Gebäude schon im Bau ist und mindestens 50% des Speichers voll ist.
        - storage_critical = 1 ist.

        Es werden keine Units rekrutiert, wenn:
        - Nicht viele Ressourcen vorhanden sind und schon eine längere Rekrutierschleife besteht.

        """
        def make_units(unit, quantity):
            """
            Just a little function which tries to recruit units
            in the given quantity.
            """
            barrack_units = ['spear', 'axe', 'sword', 'archer']
            stable_units = ['spy', 'light', 'heavy', 'marcher']
            garage_units = ['ram', 'catapult']

            if unit in barrack_units:
                self.open("barracks")

            elif unit in stable_units:
                self.open("stable")

            elif unit in garage_units:
                self.open("garage")

            else:
                print 'invalid unit: {unit}'.format(unit=unit)

            try:
                self.browser.select_form( nr = 0 )
            except mechanize.FormNotFoundError:
                print "{unit} control not found".format(unit=unit)
                return
            try:
                self.browser.form[ unit ] = str( quantity )
                self.browser.submit()
                print_cstring("Training [" + str( quantity ) + "] " + unit + "s", 'turq')
                self.statistics['units_built'][ unit ] += int(quantity)
            except mechanize.ControlNotFoundError:
                print "{unit} control not found".format(unit=unit)

        def need_to_start_light_production():
            """
            Bestimmt ob wir in der kritischen Phase sind, in der wir lkavs
            priorisieren müssen.
            """
            if self.buildings['stable'] == 3 and self.units['light']['all'] < 60:
                if self.units[ 'light' ][ 'all' ] > 0:
                    return 1
            return 0

        def unit_quest():
            """
            Just a function for the various quests.
            Supports atm just buildings spears
            """
            if self.units['spear']['all'] < 20:
                if 'id="quest_8"' in self.browser.response().read():
                    print 'You are on Quest 8!!!'
                    make_units('spear', '2')

        def default_recruit():
            """
            the standard, if no special conditions apply. stable > barracks > garage.
            """
            # Only build units if a building is under construction
            quantity = (self.buildings[ 'wood' ] / 3) + 1

            try:
                if self.units[ 'stable_time' ] < 20 * 60 or self.storage_critical:
                    if self.buildings[ 'stable' ]:
                        make_units( 'light', quantity / 3 )
            except KeyError as error:
                print "KeyError: {0}".format( error )

            if self.buildings['under_construction']:
                # TODO reevaluate try except statement


                try:
                    if self.units['barracks_time'] < 10*60 or self.storage_critical:
                        if self.buildings['barracks']:
                            make_units('axe', quantity)
                except KeyError as error:
                    print "KeyError: {0}".format(error)

                try:
                    if self.units['garage_time'] < 10*60 or self.storage_critical:
                        if self.buildings[ 'garage' ]:
                            make_units('ram', quantity / 4)
                except KeyError as error:
                    print "KeyError: {0}".format(error)


        def start_light_production():
            """
            Light production bis wir 60 haben.
            Ignore everything else.
            """

            try:
                make_units( 'light', 1 )
            except KeyError as error:
                pass

        unit_quest()

        # lights between 1 and 50
        if need_to_start_light_production():
            start_light_production()

        # else: defaulting.
        else:
            default_recruit()


    def slow_attack(self, target, units):
        """
        Usage:
        :param target: Expects a village dictionary, like those from FarmTargetHandler.raw_map
        :param units: Expects a dictionary with units in it like {'axe': 10, 'spear': 100}
        """

        # prevent errors from accessing keys, that do not exist yet
        unitlist = ['spear', 'axe', 'sword', 'spy', 'light', 'ram', 'catapult', 'knight', 'heavy']
        not_defined_units = [u for u in unitlist if u not in units.keys()]
        for u in not_defined_units:
            units[u] = 0

        self.open('place')
        #print_cstring("Attacking [{target[x]}|{target[y]}] ({target[points]} points) with payload:".format(**locals()), 'turq')
        #print_cstring('{units}'.format(**locals()), 'blue')

        self.browser.select_form( nr = 0 )
        self.browser.form[ "x" ] = str( target['x'] ) #Koordinaten des Ziels...
        self.browser.form[ "y" ] = str( target['y'] )
        self.browser.form[ "spear" ] = str( units['spear'] )
        self.browser.form[ "axe" ] = str( units['axe'] )
        self.browser.form[ "sword" ] = str( units['sword'] )
        self.browser.form[ "spy" ] = str( units['spy'] )
        self.browser.form[ "light" ] = str( units['light'] )
        self.browser.form[ "ram" ] = str( units['ram'] )
        self.browser.form[ "catapult" ] = str( units['catapult'] )
        self.browser.form[ "heavy" ] = str( units['heavy'] )

        try:
            self.browser.form[ "knight" ] = str( units['knight'] )
        except mechanize.ControlNotFoundError:
            pass
            # On some worlds there are no knights!

        self.browser.submit( )
        self.browser.select_form( nr = 0 )
        self.browser.submit( )

    def farm(self):
        """
        juicy!
        farms! is imba! doesn't make mistakes!
        makes the bot superior to humans!
        #ai = Bot(browser)
        #fth = FarmTargetHandler(ai)
        #od = fth.raw_map
        #nod = [objekt for objekt in od.items() if objekt[1]['points'] < 100 and objekt[1]['barb']]
        #ai.slow_attack(nod[2][1], {'light': 10})
        """

        def can_farm():
            """
            if we don't have units capable for farming,
            we can close the farming function immediately.
            Units capable of farming: sword/axe/light
            Not implemented: paladin. because fuck you. that's why.
            """
            if (self.units['axe']['available'] +
                self.units['sword']['available'] +
                self.units['light']['available']) <= 2:
                return 0
            else:
                return 1

        def has_no_lights( ):
            """
            Implementing farm for pre-warp civilisations.
            """
            if not self.units['light']['all']:
                return 1
            else:
                return 0

        def has_no_rams( ):
            """
            Implementing farm for pre-warp civilisations.
            """
            if not self.units['ram']['all']:
                return 1
            else:
                return 0

        def is_noob():
            """
            if we only have 20 or less
            units qualified for farming,
            this function returns 1,
            else 0.
            """
            if self.buildings['smith'] == 0:
                return 1
            else:
                return 0

        def dummy_farm():
            """
            A very simple farming function.
            Only attacks with spear/axe/sword.
            Only sends one group / target,
            attacks only targets up to distance 10.
            """
            # DECLARATIONS --------------------------------------------------------------------- #
            # units...
            spear = self.units['spear']['available']
            axe = self.units['axe']['available']
            sword = self.units['sword']['available']

            # Get a map & only attack villages with less than 75 points & distance less than 1
            atlas = self.fth.filtered_map
            atlas = OrderedDict([ objekt for objekt in atlas.items( ) if objekt[ 1 ][ 'points' ] < 75 and
                                                                         objekt[ 1 ][ 'distance' ] < 15])
            victim_gen = iter(atlas.values())
            # farmgroups...
            groups = int(axe / 2) + int(sword / 3)
            if groups > len(atlas):
                groups = len(atlas)
            if not groups:
                return 0

            spear_per_group = spear / groups
            max_spear_per_group = self.units['spear']['all'] / (int(self.units['axe']['available'] / 2 +
                                                                int(self.units['sword']['available']) / 3)) + 5
            if spear_per_group > max_spear_per_group:
                spear_per_group = max_spear_per_group
            # END OF DECLARATIONS -------------------------------------------------------------- #

            for i in range(groups):
                if axe >= 2:
                    axe -= 2
                    self.slow_attack(target=victim_gen.next(), units={'axe': 2, 'spear': spear_per_group})

                elif sword >= 3:
                    sword -= 3
                    self.slow_attack(target = victim_gen.next(), units = {'sword': 3, 'spear': spear_per_group})

                else:
                    print 'strange result in dummy_farm function. better doublecheck this.'

            print 'End of farming.\n'

        def light_farm():
            """
            A farming function for early
            civilisations with lights and no rams.
            attacks only targets up to distance 15.
            And 100 points.
            """

            # DECLARATIONS --------------------------------------------------------------------- #
            # units...
            spear = self.units[ 'spear' ][ 'available' ]
            axe = self.units[ 'axe' ][ 'available' ]
            sword = self.units[ 'sword' ][ 'available' ]
            light = self.units['light']['available']

            # Get a map & only attack villages with less than 75 points & distance less than 1
            atlas = self.fth.custom_map(points = 100, distance = 15)
            victim_gen = iter( atlas.values( ) )

            # farmgroups...
            inf_groups = axe/5 + sword/10
            kav_groups = light/2
            groups = kav_groups + inf_groups

            if groups > len( atlas ):
                groups = len( atlas )
            if not groups:
                return 0

            # split spears. 
            if inf_groups:
                spear_per_group = spear / inf_groups

            # END OF DECLARATIONS -------------------------------------------------------------- #


            for i in range( kav_groups ):
                self.slow_attack( target = victim_gen.next( ), units = { 'light': 2 } )

            for i in range( inf_groups ):
                if axe >= 2:
                    axe -= 2
                    self.slow_attack( target = victim_gen.next( ), units = { 'axe': 5, 'spear': spear_per_group } )

                elif sword >= 3:
                    sword -= 3
                    self.slow_attack( target = victim_gen.next( ), units = { 'sword': 10, 'spear': spear_per_group } )

                else:
                    print 'strange result in dummy_farm function. better doublecheck this.'



            print 'End of farming.\n'

            return 0

        def ram_farm():
            """
            We now have rams.
            Time to bash.
            Regular farming only with lights.
            """

            # FARMING PART! -------------------------------------------------------------------- #
            # DECLARATIONS --------------------------------------------------------------------- #
            # units...
            light = self.units[ 'light' ][ 'available' ]

            # Get a map & only attack villages with less than 75 points & distance less than 1
            atlas = self.fth.custom_map( points = 100, distance = 20 )
            print "found {count} potential targets.".format(count = len(atlas))
            victim_gen = iter( atlas.values( ) )

            # farmgroups...
            groups = light / 4

            if groups > len( atlas ):
                groups = len( atlas )
            # END OF DECLARATIONS -------------------------------------------------------------- #
            color = cycle(['blue', 'turq'])
            for i in range( groups ):
                victim = victim_gen.next( )
                print_cstring("[{cur}/{all}]: {string:>11} ({victim[x]}|{victim[y]})".format(cur = i+1, all = groups, string = 'Attacking', **locals()), color.next())
                self.slow_attack( target = victim, units = { 'light': 4 } )
            # END OF FARMING! ------------------------------------------------------------------ #

            # BASHING PART! -------------------------------------------------------------------- #
            # if we are low in troops, we can't bash. we will farm instead.
            # this causes strange bugs. check it. low priority
            #if self.units['axe']['all'] < 200 or self.units['ram']['all'] < 5:
            #    light_farm()
            #    return

            axe = self.units[ 'axe' ][ 'available' ]
            ram = self.units[ 'ram' ][ 'available' ]
            # if we don't have enough units, we can abort
            if axe < 170 or ram < 5:
                return

            # if the main army is not home yer, we can abort
            if 2*axe < self.units['axe']['all']:
                return

            min_points = 100
            max_points = int(axe + ram * 2)
            # only target weak targets during the night
            if datetime.datetime.now() > datetime.datetime.now().replace(hour = 22, minute=0):
                max_points = 120
            elif datetime.datetime.now() < datetime.datetime.now().replace(hour = 7):
                max_points = 120


            atlas = self.fth.custom_map(points= max_points, min_points= min_points, distance=7, rm_dangerous=False, prefer_dangerous=True, include_cleared=False)
            try:
                bash_victim = iter( atlas.values( ) ).next()
            except StopIteration:
                print 'Axis have to sleep too :)'
                return

            print_cstring("BASHING MODE ACTIVATED!", "magenta")
            print_cstring( "Attacking ({victim[x]}|{victim[y]}) with {victim[points]} points.".format(**locals()), "magenta")
            self.slow_attack(target = bash_victim, units = {'axe': axe, 'ram': ram})

            cleared = tools.toolbox.init_shelve("cleared")
            cleared[str(bash_victim['village_id'])] = 1
            cleared.close()
            return 0

        if not can_farm():
            return 0

        if is_noob():
            dummy_farm()
            return 0

        elif has_no_lights():
            dummy_farm()
            return 0

        elif has_no_rams():
            light_farm()
            return 0

        else:
            ram_farm( )


    def igm_reader(self):
        """
        A function to read ingame mails...
        """

        # linklist is a list of urls we need to visit!
        linklist = []
        self.open('mail')
        soup_source_mail = BeautifulSoup(self.browser.response().read())

        table = soup_source_mail.find_all('table', class_='vis')[2]
        igm_all = table.find_all("td", colspan = "2")

        for link in igm_all:
            if 'new_mail.png' in link.find('img')['src']:
                mail_url = link.find('a')['href']
                url = 'http://{world}.die-staemme.de{url}'.format(world=self.world, url = mail_url)
                linklist.append(url)

        for link in linklist:
            # we are now in a message we got...
            self.browser.open(link)
            soup = BeautifulSoup(self.browser.response().read())
            betreff = soup.find_all('th')[1].string

            # get author
            author = 'Author not found'
            reg = re.compile(r'.*screen=info_player')
            for element in soup.find_all('a', href=reg):
                author = element.string
                break

            print_cstring('New Message read. Title: {betreff}, From: {author}'.format(betreff = betreff.strip(),
                                                                                      author = author))

        if not linklist:
            print_cstring('No message found.')


    #def switch_village(self):
    #    """
    #    A function to switch bewtween all owned villages.
    #    """
    #    def owned_villages():
    #        """
    #        Gets a set with all Id's of the players villages.
    #        """
    #
    #        own_villages = set()
    #        self.open('overview')
    #        soup_source_html =BeautifulSoup(self.browser.response().read())
    #        table = soup_source_html.find_all('table')[21]
    #        #print table
    #        span = table.find_all('span')[0]
    #        print span
    #        village_url = span.find("a")["href"]
    #        print village_url
    #        own_villages.append(village_url)
    #        print len(own_villages)
    #        return own_villages
    #
    #    owned_villages()
    #    self.browser.open('http://{world}.die-staemme.de{url}'.format(world=self.world, url = village_id))



















