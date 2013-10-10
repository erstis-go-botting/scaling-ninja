# coding=utf-8
__author__ = 'sudo'

import ctypes
import time
import mechanize
import urllib
import ConfigParser
import os

def print_cstring(string, color='blue'):
    """
    Prettifies output.
    Makes debugging fun again.

    usage:
    print_cstring('test', 'magenta')

    :param string: Just a string you want to have printed.
    :type string: string, obviously
    :param color: the color you want to use.
    :type color: string
    """

    colors = {'red': 31, 'green': 32, 'yellow': 33, 'blue': 34, 'magenta': 35, 'turq': 36, 'white': 37}
    print "\033[%sm%s\033[0m" % (colors[color], string)

def wait_dont_sleep(seconds):
    """
    This function can be used just like time.sleep, but it
    uses the SetThreadExecutionState function
    to keep the computer awake.

    It resets the system idle timer (which determines if the
    computer should go to sleep) every 30 seconds.

    Documentation can be found here:
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa373208%28v=vs.85%29.aspx
    """
    for i in range(seconds/3):
        KERNEL32 = ctypes.windll.LoadLibrary( "Kernel32.dll" )
        ES_SYSTEM_REQUIRED = 0x00000001
        # from the MSDN:
        # ES_SYSTEM_REQUIRED
        # Forces the system to be in the working state by resetting the system idle timer.
        KERNEL32.SetThreadExecutionState( ctypes.c_int( ES_SYSTEM_REQUIRED ) )
        time.sleep(3)


def make_browser():
    # initiate the browser.
    # Cheat sheet:
    # https://views.scraperwiki.com/run/python_mechanize_cheat_sheet/?
    browser = mechanize.Browser( factory = mechanize.RobustFactory( ) )
    browser.addheaders = [ ("User-Agent",
                                 "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/17.0 Firefox/17.0") ]
    browser.set_handle_robots( False )
    return browser

def is_logged_in(browser):
    config = ConfigParser.ConfigParser( )
    config.read( r'settings\settings.ini' )

    # fetch the credentials.
    world = config.get( 'credentials', 'world' )
    # TODO CHANGE WORLD!!!
    browser.open( 'http://{world}.die-staemme.de/game.php?screen=overview&intro'.format(world=world))
    # TODO exception abfangen
    #except mechanize._response.httperror_seek_wrapper:
    #    print 'yuck'

    if '<img class="p_main"' in browser.response( ).read( ):
        print_cstring( 'Already logged in.', 'green' )
        return 1
    else:
        print_cstring( 'Currently not logged in.', 'red' )
        return 0

def login(browser):
    config = ConfigParser.ConfigParser()
    config.read( r'settings\settings.ini' )

    # fetch the credentials.
    world = config.get( 'credentials', 'world' )
    username = config.get( 'credentials', 'username' )
    password = config.get( 'credentials', 'password' )

    parameters = { 'user': username,
                   'password': password }


    data = urllib.urlencode( parameters )

    print_cstring( 'Trying to login...', 'yellow' )
    browser.open( 'http://www.die-staemme.de/index.php?action=login&server_%s' % world, data )

    if '<img class="p_main"' in browser.response( ).read( ):
        print_cstring( 'Logged in.'.format( serv = world ), 'green' )
        return 1
    else:
        print_cstring( 'Failure. Login failed on Server: {serv}'.format( serv = world ), 'red' )
        return 0

def print_startup_information():
    """
    Just some startup information
    """
    config = ConfigParser.ConfigParser( )
    config.read( r'settings\settings.ini' )

    print_cstring(time.asctime(), 'magenta')
    print ''
    print_cstring('#'*35)
    print_cstring('# {string:<20} {u:>10} #'.format(string = 'Username: ', u=os.environ['USERNAME']))
    print_cstring('# {string:<20} {c:>10} #'.format(string = 'Computername:', c=os.environ['COMPUTERNAME']))
    print_cstring('# {string:<20} {os:>10} #'.format(string = 'Operatingsystem:', os=os.environ['OS']))
    print_cstring( '#'+ ' '*33+'#' )
    print_cstring( '# {string:<20} {a:>10} #'.format( string = 'Alias: ', a = config.get( 'credentials', 'Username' ) ) )
    print_cstring('# {string:<20} {s:>10} #'.format( string = 'Server: ', s = config.get('credentials', 'world') ) )
    print_cstring( '# {string:<20} {s:>10} #'.format( string = 'Delay (in s): ', s = config.get( 'control', 'sleep' ) ) )
    print_cstring('#'*35)
    print ''