# coding=utf-8
__author__ = 'sudo'

import os
import doctest


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

