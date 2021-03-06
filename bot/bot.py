# coding=utf-8
__author__='sudo'

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
import tools.settinggen
from collections import OrderedDict
import urllib
import ConfigParser


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

        # 0 = not initialized yet
        self.village_ids=0
        # Dieser wert wird gebraucht, falls mehrere Dörfer vorhanden sind
        self.current_village=None

        self.fth=FarmTargetHandler(self)

    def construct(self):

        """
        access various information to determines if something
        should be constructed. and constructs it, if necessary.
        """

        if tools.toolbox.get_setting('control', 'do_construct')=='0':
            print 'skip constructing.'
            return

        def build(building):
            """
            constructs building
            """
            self.open('main')

            try:
                self.browser.follow_link(self.browser.find_link(url_regex=
                re.compile("upgrade_building.+id=%s"%building)))
                print_cstring("Building: [%s]"%building, 'turq')
                self.statistics['buildings_constructed']+=1
            except LinkNotFoundError:
                print_cstring('fuck that shit, not enough ressources to build [%s]'%building, 'red')

        self.open('main')
        html=self.browser.response().read()
        farm_building='\t\t\tBauernhof<br />\n\t\t\tStufe' in html
        if farm_building:
            self.pop_critical=0

        storage_building='\t\t\tSpeicher<br />\n\t\t\tStufe' in html

        if self.buildings['under_construction']:
            return

        if self.pop_critical:
            if 'farm' in self.buildable:
                build('farm')
        if self.storage_critical and 'storage' in self.buildable and not storage_building:
            build('storage')


        elif self.next_building in self.buildable and not self.pop_critical:
            build(self.next_building)

    def trade(self):
        """
        implementing basic trading...
        """

        if tools.toolbox.get_setting('control', 'do_trade')=='0':
            print 'skip trading.'
            return


        def do_trade(buy_item, sell_item, trader_count, sell_count=1000, buy_count=999, max_time=2):
            """
            the function that actually does the trade
            """
            self.open('market&mode=own_offer')
            if int(sell_count)>1000 or int(buy_count)>1000:
                print 'incorrect function usage. a trader can only carry 1k ressources'

            self.browser.select_form(nr=0)
            self.browser.form["sell"]=str(sell_count)
            self.browser.form["buy"]=str(buy_count)
            self.browser.form["res_sell"]=[str(sell_item)]
            self.browser.form["res_buy"]=[str(buy_item)]
            self.browser.form["max_time"]=str(max_time)
            self.browser.form["multi"]=str(trader_count)
            self.browser.submit()
            self.statistics['trades_conducted']+=trader_count

        self.open('market&mode=send')
        html=self.browser.response().readlines()

        #region get trader
        # get trader ----------------------------------------- #
        curtrader, maxtrader=0, 0
        for line in html:
            if re.compile(r"ndler: [0-9]+[/][0-9]+").search(line):
                curtrader, maxtrader,=map(int, re.compile(r"[0-9]+").findall(line)[:2])


        # no point in trading if we haven't got any traders...
        if not curtrader:
            return

        # create a clon of ressources to modify it to our (temporary needs)
        trading_ressources=self.ressources.copy()

        # end of get trader ---------------------------------- #
        #endregion

        # ---------------------------------------------------- ]

        #region get incoming ressources

        # Get incoming ressources ---------------------------- #
        helper=0
        for line in html:
            line=line.replace('<span class="grey">.</span>', '')

            if helper==2:


                try:
                    ressources_incoming=int(re.compile(r'\d+').findall(line)[0])
                    if 'iron' in line:
                        trading_ressources['iron']+=ressources_incoming
                    elif 'stone' in line:
                        trading_ressources['stone']+=ressources_incoming
                    elif 'wood' in line:
                        trading_ressources['wood']+=ressources_incoming
                    else:
                        print 'error: ', line

                except IndexError:
                    print 'inc'

                helper-=1

            if 'Lieferung von' in line:
                helper=2
            # End of get incoming ressources --------------------- #
        #endregion

        # ---------------------------------------------------- ]

        #region selber angebotene ressourcen

        # Ressourcen, die selber angeboten sind auslesen ----- #
        # TODO CANCEL STUFF YOU DON'T WANT TO OFFER ANYMORE
        self.open('market&mode=own_offer')
        soup=BeautifulSoup(self.browser.response().read())

        # relevant_tables beinhaltet Zeilen mit unseren Angeboten.
        try:
            relevant_tables=soup.find("table", id="own_offers_table").find_all("tr")[1:-1]
        except AttributeError:
            relevant_tables=[]

        request_type, request_amount=0, 0
        for table in relevant_tables:
            offer=table.find_all("td")[1]
            request=table.find_all("td")[2]

            offer_type=offer.span['class'][2]
            request_type=request.span['class'][2]

            offer_amount=re.findall(r'\d+', str(offer).replace('<span class="grey">.</span>', ''))[0]
            request_amount=re.findall(r'\d+', str(request).replace('<span class="grey">.</span>', ''))[0]

            trading_ressources[request_type]+=int(request_amount)
            # EOF Ressourcen die selber angeboten werden auslesen  #
        #endregion

        # ---------------------------------------------------- ]


        #region determine what to trade

        # Determine what we want to trade bitchezzzz! -------- #
        average=( trading_ressources['stone']+trading_ressources['wood']+trading_ressources['iron'] )/3
        keys=['stone', 'wood', 'iron']
        requ, offer=dict(), dict()

        for key in keys:
            difference=average-trading_ressources[key]

            if abs(difference)<1000:
                continue
            elif difference<=-1000:
                difference=abs(difference/1000)
                offer[key]=difference
            elif difference>=1000:
                difference=difference/1000
                requ[key]=difference
            else:
                print 'error in trading func'
            # EOF Determine what we want to trade ---------------- #
        #endregion

        # ---------------------------------------------------- ]


        # bei einer guten balance muessen wir nicht traden
        if not requ or not offer:
            return

        want_to_trade=sum(requ.values())
        buy, sell, count=0, 0, 0

        #region LOGIC! COOL STUFF!
        # CASE 1: We have 2 requests and not enough traders to satisfy our demands.
        # --> we just trade as much as possible for the type that needs the most.
        if len(requ)==2 and curtrader<want_to_trade:
            req_art=max(requ, key=requ.get)
            req_demand=requ[req_art]
            req_count=req_demand if req_demand<curtrader else curtrader

            offer_art=offer.keys()[0]

            buy, sell, count=req_art, offer_art, req_count


        # CASE 2: We have 2 requests and enough traders to satisfy our demands.
        elif len(requ)==2:
            offer_art=offer.keys()[0]
            for element in requ:
                req_art=element
                req_demand=requ[req_art]

                buy, sell, count=req_art, offer_art, req_demand


        # CASE 3: We have 2 offers and not enough traders to satisfy our demands.
        # --> We just give as much as possible from the ressource we have the most of. imba.
        elif len(offer)==2 and curtrader<want_to_trade:
            req_art=requ.keys()[0]

            offer_art=max(offer, key=offer.get)
            offer_support=offer[offer_art]
            offer_count=offer_support if offer_support<curtrader else curtrader

            buy, sell, count=req_art, offer_art, offer_count


        # Case 4: We have 2 offers and enough traders to satisfy our demands.
        elif len(offer)==2:
            req_art=requ.keys()[0]
            for element in offer:
                offer_art=element
                offer_support=offer[offer_art]

                buy, sell, count=req_art, offer_art, offer_support

        # Case 4: We have 1 offer and 1 request.
        elif len(offer)==1 and len(requ)==1:
            req_art=requ.keys()[0]
            offer_art=offer.keys()[0]

            count=requ[req_art] if requ[req_art]<curtrader else curtrader

            buy, sell, count=req_art, offer_art, count

        else:
            print 'Something was very strange in trade func'
            raise
            #endregion

        do_trade(buy, sell, count, max_time=2)

        print_cstring('Buying {buy} for {sell} {count} times.'.format(buy=buy, sell=sell, count=count), 'turq')

    def recruit(self):
        """
        A function to recruit units
        Units werden rekrutiert, wenn:

        - Ein Gebäude schon im Bau ist und mindestens 50% des Speichers voll ist.
        - storage_critical = 1 ist.

        Es werden keine Units rekrutiert, wenn:
        - Nicht viele Ressourcen vorhanden sind und schon eine längere Rekrutierschleife besteht.

        """
        if tools.toolbox.get_setting('control', 'do_recruit')=='0':
            print 'skip recruit.'
            return

        print 'sc', self.storage_critical
        def make_units(unit, quantity):
            """
            Just a little function which tries to recruit units
            in the given quantity.
            """
            barrack_units=['spear', 'axe', 'sword', 'archer']
            stable_units=['spy', 'light', 'heavy', 'marcher']
            garage_units=['ram', 'catapult']

            if unit in barrack_units:
                self.open("barracks")

            elif unit in stable_units:
                self.open("stable")

            elif unit in garage_units:
                self.open("garage")

            else:
                print 'invalid unit: {unit}'.format(unit=unit)

            try:
                self.browser.select_form(nr=0)
            except mechanize.FormNotFoundError:
                return

            try:
                self.browser.form[unit]=str(quantity)
                self.browser.submit()
                print_cstring("Training ["+str(quantity)+"] "+unit+"s", 'turq')
                self.statistics['units_built'][unit]+=int(quantity)
            except mechanize.ControlNotFoundError:
                return

        def need_to_start_light_production():
            """
            Bestimmt ob wir in der kritischen Phase sind, in der wir lkavs
            priorisieren müssen.
            """
            if self.buildings['stable']==3 and self.units['light']['all']<60:
                if self.units['light']['all']>0:
                    return 1
            return 0

        def unit_quest():
            """
            Just a function for the various quests.
            Supports atm just buildings spears
            """
            if self.units['spear']['all']<20:
                if 'id="quest_8"' in self.browser.response().read():
                    print 'You are on Quest 8!!!'
                    make_units('spear', '2')

        def default_recruit():
            """
            the standard, if no special conditions apply. stable > barracks > garage.
            """
            # Only build units if a building is under construction

            # just a modificator to adapt to various game phases
            mod=int(self.var_game_settings['player']['points'])/1000+1
            if mod>4:
                mod=5
            if self.storage_critical:
                mod=mod*3

            quantity=mod*2

            try:
                if self.units['stable_time']<10*60*mod:
                    if self.buildings['stable']:
                        make_units('light', quantity/3+1)
            except KeyError as error:
                print "KeyError: {0}".format(error)

            if self.buildings['under_construction']:

                try:
                    if self.units['barracks_time']<10*60*mod or self.storage_critical:
                        if self.buildings['barracks']:
                            make_units('axe', quantity/2+1)
                except KeyError as error:
                    print "KeyError: {0}".format(error)

                if self.var_game_settings['player']['villages']=='1':
                    if self.units['garage_time']<10*60 or self.storage_critical:
                        if self.buildings['garage']:
                            if self.units['ram']['all']<150:
                                make_units('ram', quantity/8+1)
                            else:
                                make_units('catapult', quantity/8+1)
                else:
                    if self.units['garage_time']<10*60 or self.storage_critical:
                        if self.buildings['garage'] and self.units['ram']['all']<250:
                            make_units('ram', quantity/8+1)

        def start_light_production():
            """
            Light production bis wir 60 haben.
            Ignore everything else.
            """

            try:
                make_units('light', 1)
            except KeyError as error:
                pass

        def deff_recruit():
            """
            For multiple villages.
            """
            if not self.buildings['under_construction']:
                return

            mod=int(self.fth.own_village['village_points'])/1000+1
            if mod>4:
                mod=5
            if self.storage_critical:
                mod*=3

            if self.units['stable_time']<10*60*mod or self.storage_critical:
                make_units('heavy', mod/3+1)

            if self.units['barracks_time']<10*60*mod or self.storage_critical:
                make_units('spear', mod+1)

        if not self.current_village:
            unit_quest()

            # lights between 1 and 50
            if need_to_start_light_production():
                start_light_production()

            # else: defaulting.
            else:
                default_recruit()
        else:
            sg=tools.settinggen.SettingGen()

            if sg.config.get(self.current_village, 'dorftyp')=='off':
                default_recruit()
            elif sg.config.get(self.current_village, 'dorftyp')=='deff':
                deff_recruit()
            else:
                print 'Invalid typ for', self.current_village, sg.config.get(self.current_village, 'dorftyp')

    def fast_attack(self, target, actioncode, template_id):
        """
        Farms really fast
        needs farmmanager.
        """
        own_village=self.var_game_settings['village']['id']
        target_id=target['village_id']

        parameters={'target': target_id,
                    'template_id': template_id,
                    'source': own_village}
        data=urllib.urlencode(parameters)

        #'village=20466&mode=farm&ajaxaction=farm&h=bc96&json=1&screen=am_farm''
        self.browser.open(
            "http://de99.die-staemme.de/game.php?screen=am_farm&village={own_village}&mode=farm&ajaxaction=farm&h={actioncode}&json=1"
            .format(
                **locals()), data)

    def combined_farm(self, target, actioncode, template_id, units):
        """
        Mit dem farmmanager kann man sehr schnell farmen, leider kann man mit ihm
        keine Menschen angreifen. Deshalb diese Funktion.
        """

        # barb --> fast_attack
        if target['barb']:
            if self.var_game_settings['player']['farm_manager']:
                self.fast_attack(target, actioncode, template_id)
            # Fastfarm doesn't work without FarmManager
            else:
                print 'Buy a farmmanager! It will speed things up ;)'
                self.slow_attack(target, units)

        # human --> slow_attack
        else:
            self.slow_attack(target, units)

    def set_get_template(self, units):
        """
        Setzt ein neues template beim farm-assistent und gibt dessen Nummer zurück
        """
        unitlist=['spear', 'axe', 'sword', 'spy', 'light', 'heavy']
        not_defined_units=[u for u in unitlist if u not in units.keys()]
        for u in not_defined_units:
            units[u]=0

            self.open("am_farm")

        self.browser.select_form(nr=0)

        self.browser.form["spear"]=str(units['spear'])
        self.browser.form["axe"]=str(units['axe'])
        self.browser.form["sword"]=str(units['sword'])
        self.browser.form["spy"]=str(units['spy'])
        self.browser.form["light"]=str(units['light'])
        self.browser.form["heavy"]=str(units['heavy'])

        self.browser.submit()

        self.open("am_farm")
        self.get_var_game_data(locale=True)

        actioncode=self.var_game_settings['csrf']
        templatenr=re.search(r'template_id=(\d+)', self.browser.response().read()).group(1)

        return actioncode, templatenr

    def slow_attack(self, target, units):
        """
        Usage:
        :param target: Expects a village dictionary, like those from FarmTargetHandler.raw_map
        :param units: Expects a dictionary with units in it like {'axe': 10, 'spear': 100}
        """

        # prevent errors from accessing keys, that do not exist yet
        unitlist=['spear', 'axe', 'sword', 'spy', 'light', 'ram', 'catapult', 'knight', 'heavy']
        not_defined_units=[u for u in unitlist if u not in units.keys()]
        for u in not_defined_units:
            units[u]=0

        self.open('place')
        #print_cstring("Attacking [{target[x]}|{target[y]}] ({target[points]} points) with payload:".format(**locals()), 'turq')
        #print_cstring('{units}'.format(**locals()), 'blue')

        self.browser.select_form(nr=0)
        self.browser.form["x"]=str(target['x']) #Koordinaten des Ziels...
        self.browser.form["y"]=str(target['y'])
        self.browser.form["spear"]=str(units['spear'])
        self.browser.form["axe"]=str(units['axe'])
        self.browser.form["sword"]=str(units['sword'])
        self.browser.form["spy"]=str(units['spy'])
        self.browser.form["light"]=str(units['light'])
        self.browser.form["ram"]=str(units['ram'])
        self.browser.form["catapult"]=str(units['catapult'])
        self.browser.form["heavy"]=str(units['heavy'])

        try:
            self.browser.form["knight"]=str(units['knight'])
        except mechanize.ControlNotFoundError:
            pass
            # On some worlds there are no knights!
        self.browser.submit()
        self.browser.select_form(nr=0)
        self.browser.submit()

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

        if tools.toolbox.get_setting('control', 'do_farm')=='0':
            print 'skip farming.'
            return

        def can_farm():
            """
            if we don't have units capable for farming,
            we can close the farming function immediately.
            Units capable of farming: sword/axe/light
            Not implemented: paladin. because fuck you. that's why.
            """
            if (self.units['axe']['available']+
                    self.units['sword']['available']+
                    self.units['light']['available'])<=2:
                return 0
            else:
                return 1

        def has_no_lights():
            """
            Implementing farm for pre-warp civilisations.
            """
            if not self.units['light']['all']:
                return 1
            else:
                return 0

        def has_no_rams():
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
            if self.buildings['smith']==0:
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
            spear=self.units['spear']['available']
            axe=self.units['axe']['available']
            sword=self.units['sword']['available']

            # Get a map & only attack villages with less than 75 points & distance less than 1
            atlas=self.fth.filtered_map
            atlas=OrderedDict([objekt for objekt in atlas.items() if objekt[1]['points']<75 and
                                                                     objekt[1]['distance']<15])
            victim_gen=iter(atlas.values())
            # farmgroups...
            groups=int(axe/2)+int(sword/3)
            if groups>len(atlas):
                groups=len(atlas)
            if not groups:
                return 0

            spear_per_group=spear/groups
            max_spear_per_group=self.units['spear']['all']/(int(self.units['axe']['available']/2+
                                                                int(self.units['sword']['available'])/3))+5
            if spear_per_group>max_spear_per_group:
                spear_per_group=max_spear_per_group
                # END OF DECLARATIONS -------------------------------------------------------------- #

            for i in range(groups):
                if axe>=2:
                    axe-=2
                    self.slow_attack(target=victim_gen.next(), units={'axe': 2, 'spear': spear_per_group})

                elif sword>=3:
                    sword-=3
                    self.slow_attack(target=victim_gen.next(), units={'sword': 3, 'spear': spear_per_group})

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
            spear=self.units['spear']['available']
            axe=self.units['axe']['available']
            sword=self.units['sword']['available']
            light=self.units['light']['available']

            # Get a map & only attack villages with less than 75 points & distance less than 1
            atlas=self.fth.custom_map(points=100, distance=15)
            victim_gen=iter(atlas.values())

            # farmgroups...
            inf_groups=axe/5+sword/10
            kav_groups=light/2
            groups=kav_groups+inf_groups

            if groups>len(atlas):
                groups=len(atlas)
            if not groups:
                return 0

            # split spears. 
            if inf_groups:
                spear_per_group=spear/inf_groups

            # END OF DECLARATIONS -------------------------------------------------------------- #


            for i in range(kav_groups):
                self.slow_attack(target=victim_gen.next(), units={'light': 2})

            for i in range(inf_groups):
                if axe>=2:
                    axe-=2
                    self.slow_attack(target=victim_gen.next(), units={'axe': 5, 'spear': spear_per_group})

                elif sword>=3:
                    sword-=3
                    self.slow_attack(target=victim_gen.next(), units={'sword': 10, 'spear': spear_per_group})

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
            light=self.units['light']['available']

            # fakebegrenzung kann in den weg kommen
            point_minimum_lkav=self.fth.own_village['village_points']/300
            light_to_send=4
            if light_to_send<point_minimum_lkav:
                light_to_send=point_minimum_lkav
            lk_max_points=light_to_send*25
            lk_max_points=200 if lk_max_points>200 else lk_max_points

            # Get a map & only attack villages with less than 75 points & distance less than 1
            atlas=self.fth.custom_map(points=lk_max_points, distance=30)
            print "found {count} potential targets.".format(count=len(atlas))
            victim_gen=iter(atlas.values())


                # END OF DECLARATIONS -------------------------------------------------------------- #
            # ATTACKING!
            try:
                barb_send=int(self.config.get('control', 'split'))
            except ConfigParser.NoOptionError:
                print 'specify an integer under [control] -> split (in settings.ini)'
                print 'defaulting to 5'
                barb_send=5

            print_cstring('Farming with {barb_send}/{light_to_send} LKavs:'.format(**locals()), 'green')

            barb_send=barb_send if light_to_send>barb_send else light_to_send
            ac, tn=self.set_get_template({'light': barb_send})

            color=cycle(['blue', 'turq'])
            while light>=light_to_send:
                try:
                    victim=victim_gen.next()
                except StopIteration:
                    print 'sir farm alot strikes again.'
                    atlas=self.fth.custom_map(points=lk_max_points, distance=30, rm_under_attack=False)
                    victim_gen=iter(atlas.values())
                    victim=victim_gen.next()

                if victim['barb']:
                    send=barb_send
                else:
                    send=light_to_send

                helper_string="[{cur}/{all}]:".format(cur=light, all=self.units['light']['available'])
                print_cstring("# {helper_string:<10} Attacking {village_name:<25} ({victim[x]}|{victim[y]}) #".format(
                    village_name=victim['village_name'].encode('utf-8'), **locals()), color.next())

                self.combined_farm(target=victim, units={'light': send}, template_id=tn, actioncode=ac)
                light-=send

            axe=self.units['axe']['available']
            ram=self.units['ram']['available']
            spies=self.units['spy']['available']
            cat=self.units['catapult']['available']

            # if we don't have enough units, we can abort
            if axe<170 or ram<5:
                return

            # if the main army is not home yet, we can abort
            if 2*axe<self.units['axe']['all']:
                return

            min_points=lk_max_points
            max_points=int(axe*0.8+ram)

            distance=7

            # only target weak targets during the night but in a slightly bigger radius
            if datetime.datetime.now()>datetime.datetime.now().replace(hour=22, minute=0):
                max_points/=4
                if max_points>500:
                    max_points=500
                distance=8
            elif datetime.datetime.now()<datetime.datetime.now().replace(hour=7):
                max_points/=4
                if max_points>500:
                    max_points=500
                distance=8

            atlas=self.fth.custom_map(points=max_points, min_points=min_points, distance=distance, rm_dangerous=False,
                                      prefer_dangerous=True, include_cleared=False)
            try:
                bash_gen=iter(atlas.values())
                bash_victim=bash_gen.next()
                if "1575921120"==bash_victim['player_id'] or '1575889856'==bash_victim['player_id']:
                    print 'manual ram stuff [dont attack my lovely deffer]'
                    bash_victim=bash_gen.next()

            except StopIteration:
                print 'Axis have to sleep too :)'
                return

            print_cstring("BASHING MODE ACTIVATED!", "magenta")
            village_name=bash_victim['village_name'].encode("utf-8")
            print_cstring(
                "Attacking {village_name} ({bash_victim[x]}|{bash_victim[y]}) with {bash_victim[points]} points. ".format(**locals()),
                "magenta")
            self.slow_attack(target=bash_victim, units={'axe': axe, 'ram': ram, 'spy': spies, 'catapult': cat})

            cleared=tools.toolbox.init_shelve("cleared")
            cleared[str(bash_victim['village_id'])]=1
            cleared.close()

            # safaly mark cleared villages.
            village_id=str(bash_victim['village_id'])
            if not self.add_to_marked_group(village_id, "CLEAR"):
                print 'GROUP CLEAR NOT FOUND. CREATING IT!'
                self.mark_village(village_id, "CLEAR", red="127", blue="240", green="240")

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
            ram_farm()

    def igm_reader(self):
        """
        A function to read ingame mails...
        """

        linklist=[]
        self.open('mail')
        soup_source_mail=BeautifulSoup(self.browser.response().read())

        table=[t for t in soup_source_mail.find_all('table', class_='vis') if "mail.png" in str(t) if 'screen=info_player">' in str(t)][0]
        igm_all=table.find_all("td", colspan="2")

        for link in igm_all:
            if 'new_mail.png' in link.find('img')['src']:
                mail_url=link.find('a')['href']
                url='http://{world}.die-staemme.de{url}'.format(world=self.world, url=mail_url)
                linklist.append(url)

        for link in linklist:
            # we are now in a message we got...
            self.browser.open(link)
            soup=BeautifulSoup(self.browser.response().read())
            betreff=soup.find_all('th')[1].string

            # get author
            author='Author not found'
            reg=re.compile(r'.*screen=info_player')
            for element in soup.find_all('a', href=reg):
                author=element.string
                break

            print_cstring('New Message read. Title: {betreff}. From: {author}'.format(betreff=betreff.strip(),
                                                                                      author=author))

        if not linklist:
            print_cstring('No message found.')

    def mark_village(self, village_id, name, red, blue, green):
        """
a
        """

        print village_id
        self.open("village_color&village_id={village_id}".format(**locals()))

        self.browser.select_form(nr=0)

        self.browser["name"]=name
        self.browser["color_picker_r"]=red
        self.browser["color_picker_b"]=blue
        self.browser["color_picker_g"]=green

        self.browser.submit()

    def add_to_marked_group(self, village_id, groupname):
        """
        Fügt ein Dorf zu einer Gruppe der Karte hinzu
        Falls diese Gruppe nicht existiert, wird 0 zurückgegeben.
        """

        self.open("village_color&village_id={village_id}".format(**locals()))
        soup=BeautifulSoup(self.browser.response().read())
        links=soup.find_all("a")

        try:
            grouplink=[element for element in links if element.string==groupname][0]
        except IndexError:
            return 0

        self.browser.open('http://{self.world}.die-staemme.de'.format(**locals())+grouplink['href'])
        return 1

    def make_coins(self):
        """
        Makes coins, yay
        """

        if tools.toolbox.get_setting('control', 'make_coins')=='0':
            return
        if not tools.toolbox.get_setting('control', 'make_coins'):
            return
        if not self.buildings['snob']:
            return

        print 'Woah, will münzen prägen!!!'

        self.open("snob")
        soup=BeautifulSoup(self.browser.response().read())

        link=[s for s in soup.find_all("a") if "action=coin" in s.get("href")]
        if not link:
            return

        link=link[0].get("href")

        self.browser.open('http://{self.world}.die-staemme.de{link}'.format(**locals()))

        print 'made a coin! :)'

    def multiplevillages(self):
        """
        handles crazy multiple villages stuff
        """

        if self.var_game_settings['player']['villages']=='1':
            return 0

        village_id_name=self.get_village_ids()
        sgenerator=tools.settinggen.SettingGen()

        self.village_ids=village_id_name.keys()

        # Generate settings with default values if there is a new village
        for id_ in village_id_name.keys():
            if not sgenerator.config.has_section(str(id_)):
                sgenerator.generate_skeleton(id_, village_id_name[id_])
                print_cstring('New village found: {id_}. Generated an entry with default values.'.format(**locals()), 'green')

        print 'Villages: ', self.var_game_settings['player']['villages']
        return 1

    def multiplevillages_handler(self):
        """
        do's everything for multiple villages
        """
        if len(self.village_ids)<2:
            print 'What am I even doing here? GTFO multiplevillages_handler'
            exit()

        for village in self.village_ids:
            print 'VILLAGE: {village}'.format(village=village)
            self.open("overview", village=village)

            self.refresh_all()
            self.refresh_map()
            self.current_village=village
            sg=tools.settinggen.SettingGen()

            if sg.config.get(village, 'do_construct')=='1':
                self.construct()

            if sg.config.get(village, 'do_recruit')=='1':
                self.recruit()

            if sg.config.get(village, 'do_trade')=='1':
                self.trade()

            if sg.config.get(village, 'do_farm')=='1':
                self.farm()

            if sg.config.get(village, 'make_coins')=='1':
                self.make_coins()

            self.close()

    def botloop(self):
        """
        DO EVERYTHING!!!!
        """
        self.construct()
        self.recruit()
        self.trade()
        self.farm()
        self.make_coins()
        self.close()

    def refresh_map(self):
        """
        Creates a new map
        """
        del self.fth
        self.fth=FarmTargetHandler(self)