# coding=utf-8
__author__ = 'sudo'

import re
from bs4 import BeautifulSoup
from mechanize._mechanize import LinkNotFoundError
from tools.toolbox import print_cstring
from crawl.botContainer import BotContainer
import mechanize

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
    def __init__(self):
        BotContainer.__init__(self)


        # is the storage very full?
        for element in ['stone', 'wood', 'iron']:
            if self.ressources[element] > self.ressources['storage'] * 0.7:
                self.storage_critical = 1
                break
            else:
                self.storage_critical = 0

        # is the farm very full?
        if self.ressources['pop_now'] > self.ressources['pop_max'] * 0.75:
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
                print_cstring("Building: [%s]" % building, 'yellow')
            except LinkNotFoundError:
                print_cstring( 'fuck that shit, not enough ressources to build [%s]' % building, 'red')

        if self.pop_critical and 'farm' in self.buildable:
            build( 'farm' )
        elif self.storage_critical and 'storage' in self.buildable:
            build('storage')
        elif self.next_building in self.buildable:
            build(self.next_building)

    def trade(self):
        """
        implementing basic trading...
        """

        def do_trade(buy_item, sell_item, trader_count, sell_count=1000, buy_count=999, max_time = 5):
            """
            the function that actually does the trade
            """
            self.open('market&mode=own_offer')
            if int(sell_count) > 1000 or int(buy_count) > 1000:
                print 'incorrect function usage. a trader can only carry 1k ressources'
                print 'go fuck yourself.'

            self.browser.select_form( nr = 0 )
            self.browser.form[ "sell" ] = str(sell_count)
            self.browser.form[ "buy" ] = str(buy_count)
            self.browser.form[ "res_sell" ] = [ str( sell_item ) ]
            self.browser.form[ "res_buy" ] = [ str( buy_item ) ]
            self.browser.form[ "max_time" ] = str( max_time )
            self.browser.form[ "multi" ] = str( trader_count )
            self.browser.submit( )


        self.open( 'market&mode=send' )
        html = self.browser.response( ).readlines( )

        #region get trader
        # get trader ----------------------------------------- #
        curtrader, maxtrader = 0, 0
        for line in html:
            if re.compile( r"ndler: [0-9]+[/][0-9]+" ).search( line ):
                curtrader, maxtrader, = map(int, re.compile( r"[0-9]+" ).findall( line )[ :2 ])

        print "Trader: [{curtrader}/{maxtrader}]".format(**locals())

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
            print 'I will request {req_count} {req_art} and I will offer {offer_art}'.format(**locals())


        # CASE 2: We have 2 requests and enough traders to satisfy our demands.
        elif len(requ) == 2:
            offer_art = offer.keys()[0]
            for element in requ:
                req_art = element
                req_demand = requ[req_art]

                buy, sell, count = req_art, offer_art, req_demand
                print 'I will request {req_demand} {req_art} and I will offer {offer_art}'.format(**locals())


        # CASE 3: We have 2 offers and not enough traders to satisfy our demands.
        # --> We just give as much as possible from the ressource we have the most of. imba.
        elif len(offer) == 2 and curtrader < want_to_trade:
            req_art = requ.keys()[0]

            offer_art = max( offer, key = offer.get )
            offer_support = offer[offer_art]
            offer_count = offer_support if offer_support < curtrader else curtrader

            buy, sell, count = req_art, offer_art, offer_count
            print 'I will request {offer_count} {req_art} and I will offer {offer_art}'.format(**locals())


        # Case 4: We have 2 offers and enough traders to satisfy our demands.
        elif len(offer) == 2:
            req_art = requ.keys( )[ 0 ]
            for element in offer:
                offer_art = element
                offer_support = offer[offer_art]

                buy, sell, count = req_art, offer_art, offer_support
                print 'I will request {offer_support} {req_art} and I will offer {offer_art}'.format(**locals())

        # Case 4: We have 1 offer and 1 request.
        elif len(offer) == 1 and len(requ) == 1:
            req_art = requ.keys()[0]
            offer_art = offer.keys()[0]

            count = requ[req_art] if requ[req_art] < curtrader else curtrader

            print 'I will request {count} {req_art} and I will offer {offer_art}'.format(**locals())
            buy, sell, count = req_art, offer_art, count

        else:
            print 'Something was very strange in trade func'
            raise
        #endregion

        do_trade(buy, sell, count, max_time=3)

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
            barrack_units = ['spear', 'axe', 'sword', 'archer']
            if unit in barrack_units:
                self.open("barracks")

                self.browser.select_form( nr = 0 )
                try:
                    self.browser.form[ unit ] = str( quantity )
                    self.browser.submit( )
                    print "Training [" + str( quantity ) + "] " + unit + "s"

                except mechanize.ControlNotFoundError:
                    print "Units are unavailable"

        if self.units['barracks_time'] < 10:
            make_units('axe', 10)




















