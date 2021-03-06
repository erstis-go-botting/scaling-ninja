# coding=utf-8
__author__ = 'sudo'

import ctypes
import time
import mechanize
import urllib
import ConfigParser
import os
import math
import shelve
import deathbycaptcha
import re
import datetime

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
    browser.open( 'http://{world}.die-staemme.de/game.php?screen=overview'.format(world=world))
    #except mechanize._response.httperror_seek_wrapper:
    #    print 'yuck'

    if '<img class="p_main"' in browser.response( ).read( ):
        print_cstring('Logged in.', 'green')
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

    if is_logged_in(browser):
        return 1
    else:
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


def init_shelve(filename):
    """
    expects a valid filename as input
    outputs a shelve object
    """

    conf = ConfigParser.ConfigParser()
    conf.read( r'settings/settings.ini' )
    path = os.path.abspath(conf.get( 'storage', 'path' ))

    resulting_path = os.path.join(path, filename)

    my_shelve = shelve.open(resulting_path, writeback=True)
    #if not os.path.exists(resulting_path):

    return my_shelve


def botprot(browser):
    """
    Class dedicated to captcha handling.
    Fun stuff. (deep magic)
    """

    #config = ConfigParser.ConfigParser()
    #config.read('settings.ini')
    #world = config.get('login', 'server')
    #
    #browser.open("http://"+str(world)+".die-staemme.de/game.php?screen=main")
    #botprot = 0
    #for line in browser.response().readlines():
    #    if 'Botschutz' in line:
    #        botprot = 1
    #if botprot:

    config = ConfigParser.ConfigParser( )
    config.read( r'settings\settings.ini' )

    # fetch the credentials.
    world = config.get( 'credentials', 'world' )
    user = config.get( 'credentials', 'captcha_user' )
    pw = config.get( 'credentials', 'captcha_pass' )


    browser.retrieve('http://'+world+'.die-staemme.de/human.png', 'ca.png')
    time.sleep(1)
    client = deathbycaptcha.SocketClient(user, pw)
    try:
        balance = client.get_balance()
        print_cstring('DEATHBYCAPTCHA Balance: [%s]' % balance, 'magenta')
        if int(balance) < 50:
            print 'BALANCE VERY LOW!!!'

        captcha = client.decode("ca.png")
        if captcha:
        # The CAPTCHA was solved; captcha["captcha"] item holds its
            # numeric ID, and captcha["text"] item its text.
            print_cstring( "I think I solved it: %s" % (captcha["text"]), 'red')

    # Access to DBC API denied, check your credentials and/or balance
    except deathbycaptcha.AccessDeniedException:
        print "DENIED!!!"
        return 0


    browser.select_form(nr=0)
    try:
        browser.form["code"] = str(captcha["text"])
    except TypeError:
        print 'TypeError'
    browser.submit()

    if "bot_check" in browser.response().read():
        print_cstring('Bad captcha, trying again.', 'magenta')
        browser.open('http://'+world+'.die-staemme.de')
        botprot(browser)
        #client.report(captcha["captcha"])
    else:
        print_cstring( 'Captcha solved, fuck the system :)', 'green')


def parse_time( time_string ):
    """
    takes something like
    u'13.10.13 20:46'
    "am 07.11. um 07:54:06 Uhr"
    "morgen um ..."

    returns a datetime object
    """
    split_time=re.findall('\d+', time_string)
    if "heute um" in time_string:
        day=datetime.datetime.today().day
        year=datetime.datetime.today().year
        month=datetime.datetime.today().month

        hour=int(split_time[0])
        minute=int(split_time[1])

    elif "morgen um" in time_string:
        day=datetime.datetime.today().day+1
        year=datetime.datetime.today().year
        month=datetime.datetime.today().month

        hour=int(split_time[0])
        minute=int(split_time[1])

    elif "am" in time_string:
        day=int(split_time[0])
        month=int(split_time[1])
        year=year=datetime.datetime.today().year

        hour=int(split_time[2])
        minute=int(split_time[3])

    else:
        day=int(split_time[0])
        month=int(split_time[1])
        year=int('20'+split_time[2])

        hour=int(split_time[3])
        minute=int(split_time[4])

    time_object = datetime.datetime( day = day, month = month, year = year, hour= hour, minute= minute )

    return time_object


def get_setting(argument1, argument2):
    """
    Returns none if nothing is found,
    else the setting.
    """
    config=ConfigParser.ConfigParser()
    config.read(r'settings\settings.ini')

    # fetch the credentials.
    try:
        setting=config.get(argument1, argument2)
    except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
        print 'Invalid arguments [{argument1}] {argument2}. Defaulting to standard settings.'.format(**locals())
        setting=None

    return setting


def calculate_distance(x1, y1, x2, y2):
    """
    just returns the distance
    """
    x1, x2, y1, y2=int(x1), int(x2), int(y1), int(y2)
    return math.sqrt((x1-x2)**2+(y1-y2)**2)