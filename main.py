# coding=utf-8
__author__ = 'sudo'


from bot.bot import Bot
from tools.toolbox import print_cstring, wait_dont_sleep
import thread
from pprint import pprint
import tools.toolbox
from crawl.dataminer import FarmTargetHandler

def main(br):
    ai = Bot(br)
    ai.construct()
    ai.recruit()
    ai.trade()
    ai.close()
    fth = FarmTargetHandler( ai )

    print_cstring( '\nRank: ' + ai.var_game_settings[ 'player' ][ 'rank' ], 'blue' )

    igm = int(ai.var_game_settings['player']['new_igm'])
    if igm:
        print_cstring('You got new ingame messages!'.format(**locals()), 'magenta')

    print '\nStatistics:'
    pprint(ai.statistics)
    print_cstring('#'*100+'\n', 'yellow')


browser = tools.toolbox.make_browser()

#ai = Bot(browser)
#fth = FarmTargetHandler(ai)
#od = fth.raw_map
#nod = [objekt for objekt in od.items() if objekt[1]['points'] < 100 and objekt[1]['barb']]
#ai.slow_farm(nod[2][1], {'light': 10})


while 1:
    thread.start_new_thread( main, (browser,) )

    # Don't allow sleep/hibernate! Deep magic.
    wait_dont_sleep(400)
