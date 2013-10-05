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

    print '\nStatistics:\n'
    pprint(ai.statistics)
    print ''

    print_cstring('#'*100, 'yellow')


while 1:
    thread.start_new_thread(main, tuple())
    time.sleep(500)