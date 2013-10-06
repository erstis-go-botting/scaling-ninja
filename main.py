# coding=utf-8
__author__ = 'sudo'


from bot.bot import Bot
from tools.toolbox import print_cstring, wait_dont_sleep
import thread
from pprint import pprint
import tools.toolbox

def main(br):
    ai = Bot(br)
    ai.construct()
    ai.recruit()
    ai.trade()
    ai.close()

    print_cstring( '\nRank: ' + ai.var_game_settings[ 'player' ][ 'rank' ], 'blue' )

    igm = int(ai.var_game_settings['player']['new_igm'])
    modifier = 's' if igm > 1 else ''
    if igm:
        print_cstring('You got {igm} new ingame message{modifier}!'.format(**locals()), 'red')

    print '\nStatistics:'
    pprint(ai.statistics)
    print_cstring('#'*100+'\n', 'yellow')


browser = tools.toolbox.make_browser()
while 1:
    if tools.toolbox.is_logged_in(browser):
        thread.start_new_thread(main, (browser,))
    else:
        if tools.toolbox.login(browser):
            thread.start_new_thread(main, (browser,))
        # bei einem nicht erfolgreichen login versuchen wir es einfach später noch einmal

    wait_dont_sleep(400)
