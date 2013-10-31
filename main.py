# coding=utf-8
__author__ = 'sudo'


from bot.bot import Bot
from tools.toolbox import print_cstring, wait_dont_sleep
import thread
import tools.toolbox
from ConfigParser import ConfigParser
import time

tools.toolbox.print_startup_information()

def main(br):
    print(time.asctime())
    soul = Bot(br)

    if soul.multiplevillages():
        soul.multiplevillages_handler()
    else:
        soul.botloop()

    #print_cstring( '\nRank: ' + soul.var_game_settings[ 'player' ][ 'rank' ], 'blue' )

    igm = int(soul.var_game_settings['player']['new_igm'])
    if igm:
        print_cstring('You got new ingame messages!'.format(**locals()), 'magenta')
        soul.igm_reader()

    print_cstring('#'*100+'\n', 'yellow')

    #soul.switch_village()

    #for village_id in own_village:
    #    """
    #    Schleife für mehrere Dörfer hier:
    #    """

browser = tools.toolbox.make_browser()

if __name__ == '__main__':
    while 1:
        thread.start_new_thread( main, (browser,) )

        config = ConfigParser()
        config.read( r'settings\settings.ini' )

        # Don't allow sleep/hibernate! Deep magic.
        wait_dont_sleep(config.getint('control', 'sleep'))