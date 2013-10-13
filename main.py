# coding=utf-8
__author__ = 'sudo'


from bot.bot import Bot
from tools.toolbox import print_cstring, wait_dont_sleep
import thread
from pprint import pprint
import tools.toolbox
from crawl.dataminer import FarmTargetHandler
from ConfigParser import ConfigParser
import time

tools.toolbox.print_startup_information()

def main(br):
    print(time.asctime())
    soul = Bot(br)
    soul.construct()
    soul.recruit()
    soul.trade()
    soul.farm()
    soul.close()
    fth = FarmTargetHandler( soul )

    print_cstring( '\nRank: ' + soul.var_game_settings[ 'player' ][ 'rank' ], 'blue' )

    igm = int(soul.var_game_settings['player']['new_igm'])
    if igm:
        print_cstring('You got new ingame messages!'.format(**locals()), 'magenta')


    #soul.igm_reader()
    # buggy atm

    print_cstring('#'*100+'\n', 'yellow')


browser = tools.toolbox.make_browser()
while 1:
    thread.start_new_thread( main, (browser,) )

    config = ConfigParser()
    config.read( r'settings\settings.ini' )

    # Don't allow sleep/hibernate! Deep magic.
    wait_dont_sleep(config.getint('control', 'sleep'))
