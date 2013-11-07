# coding=utf-8
__author__ = 'sudo'

from bs4 import BeautifulSoup

# BeautifulSoup Documentation:
# http://www.crummy.com/software/BeautifulSoup/bs4/doc/

def find_all_links(soup):
    """
    Needs a soup element
    -> returns all links from a page.
    """
    for link in soup.find_all('a'):
        print link.get('href')


def has_class_but_no_id(tag):
    return tag.name==u'td' and not tag.has_attr('id') and tag.get('class')==[u'nowrap']


soup=BeautifulSoup(None) # replace None with something cool obviously
soup.find_all(has_class_but_no_id)

#[<td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'spear')"><img alt="" class="" src="http://cdn2
# .tribalwars.net/8.16/18968/graphic/unit/unit_spear.png?48b3b" title="Speerträger"/></a> <input class="unitsInput" id="unit_input_spear"
# name="spear" style="width: 40px" tabindex="1" type="text" value=""/> <a href="javascript:insertUnit($('#unit_input_spear'),
# 534)">(534)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'sword')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_sword.png?b389d" title="Schwertkämpfer"/></a> <input class="unitsInput"
# id="unit_input_sword" name="sword" style="width: 40px" tabindex="2" type="text" value=""/> <a href="javascript:insertUnit($(
# '#unit_input_sword'), 0)">(0)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'axe')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_axe.png?51d94" title="Axtkämpfer"/></a> <input class="unitsInput"
# id="unit_input_axe" name="axe" style="width: 40px" tabindex="3" type="text" value=""/> <a href="javascript:insertUnit($(
# '#unit_input_axe'), 60)">(60)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'spy')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_spy.png?eb866" title="Späher"/></a> <input class="unitsInput"
# id="unit_input_spy" name="spy" style="width: 40px" tabindex="4" type="text" value=""/> <a href="javascript:insertUnit($(
# '#unit_input_spy'), 0)">(0)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'light')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_light.png?2d86d" title="Leichte Kavallerie"/></a> <input
# class="unitsInput" id="unit_input_light" name="light" style="width: 40px" tabindex="5" type="text" value=""/> <a
# href="javascript:insertUnit($('#unit_input_light'), 10)">(10)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'heavy')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_heavy.png?a83c9" title="Schwere Kavallerie"/></a> <input
# class="unitsInput" id="unit_input_heavy" name="heavy" style="width: 40px" tabindex="6" type="text" value=""/> <a
# href="javascript:insertUnit($('#unit_input_heavy'), 136)">(136)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'ram')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_ram.png?2003e" title="Rammbock"/></a> <input class="unitsInput"
# id="unit_input_ram" name="ram" style="width: 40px" tabindex="7" type="text" value=""/> <a href="javascript:insertUnit($(
# '#unit_input_ram'), 10)">(10)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'catapult')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_catapult.png?5659c" title="Katapult"/></a> <input class="unitsInput"
# id="unit_input_catapult" name="catapult" style="width: 40px" tabindex="8" type="text" value=""/> <a href="javascript:insertUnit($(
# '#unit_input_catapult'), 0)">(0)</a>
#</td>, <td class="nowrap"><a class="unit_link" href="#" onclick="return UnitPopup.open(event, 'snob')"><img alt="" class=""
# src="http://cdn2.tribalwars.net/8.16/18968/graphic/unit/unit_snob.png?0019c" title="Adelsgeschlecht"/></a> <input class="unitsInput"
# id="unit_input_snob" name="snob" style="width: 40px" tabindex="9" type="text" value=""/> <a href="javascript:insertUnit($(
# '#unit_input_snob'), 0)">(0)</a>
#</td>]
