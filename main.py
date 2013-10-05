# coding=utf-8
__author__ = 'sudo'


from crawl.botContainer import BotContainer
from bot.bot import Bot
from crawl.dataminer import FarmTargetHandler
from tools.toolbox import print_cstring
import time
import thread
from pprint import pprint


def main():
    ai = Bot()
    ai.construct()
    ai.trade()
    ai.recruit()
    ai.close()

    print_cstring( '\nRank: ' + ai.var_game_settings[ 'player' ][ 'rank' ], 'blue' )

    igm = int(ai.var_game_settings['player']['new_igm'])
    modifier = 's' if igm > 1 else ''
    if igm:
        print_cstring('You got {igm} new ingame message{modifier}!'.format(**locals()), 'red')

    print '\nStatistics:'
    pprint(ai.statistics)

    print_cstring('#'*100+'\n', 'yellow')


while 1:
    thread.start_new_thread(main, tuple())
    time.sleep(500)