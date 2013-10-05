# coding=utf-8
__author__ = 'sudo'


from crawl.botContainer import BotContainer
from bot.bot import Bot
from crawl.dataminer import FarmTargetHandler
from tools.toolbox import print_cstring
import time
import thread



def main():
    ai = Bot()
    ai.construct()
    ai.trade()
    ai.recruit()

    if ai.config.getint( 'control', 'pause' ):
        print 'EXECUTION PAUSED'
        return

    # TODO ASK FOR PREMIUM
    # TODO http://www.jetbrains.com/teamcity/

    #print data.units
    #print data.ressources
    #print data.var_game_settings

    print_cstring('Rank: '+ ai.var_game_settings['player']['rank'], 'red')


    print '#'*100


while 1:
    thread.start_new_thread(main, tuple())
    time.sleep(500)