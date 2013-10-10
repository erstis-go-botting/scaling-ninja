# coding=utf-8
__author__ = 'sudo'

from bs4 import BeautifulSoup
import re

# BeautifulSoup Documentation:
# http://www.crummy.com/software/BeautifulSoup/bs4/doc/

def find_all_links(soup):
    """
    Needs a soup element
    -> returns all links from a page.
    """
    for link in soup.find_all('a'):
        print link.get('href')