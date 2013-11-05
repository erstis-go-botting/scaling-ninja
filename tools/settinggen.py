# coding=utf-8
import ConfigParser


class SettingGen(object):
    def __init__(self):
        self.config=ConfigParser.SafeConfigParser()
        self.config.read("settings/settings.ini")
        self.settingpath=self.config.get('storage', 'worldsettingspath')
        self.config=ConfigParser.SafeConfigParser(allow_no_value=True)
        self.config.read(self.settingpath)
        if not self.config.has_section('description'):
            self.generate_description()

    def generate_skeleton(self, village_id, village_name):
        """
        Generates the standard skeleton
        """

        village_id=str(village_id)

        if self.config.has_section(village_id):
            print 'woah, stop right there, that shit allready exists.'
            return

        self.config.add_section(village_id)

        self.config.set(village_id, '# {village_name}'.format(**locals()))
        self.config.set(village_id, 'make_coins', '0')
        self.config.set(village_id, 'do_trade', '1')
        self.config.set(village_id, 'do_recruit', '1')
        self.config.set(village_id, 'do_farm', '1')
        self.config.set(village_id, 'do_construct', '1')
        self.config.set(village_id, 'church', '0')
        self.config.set(village_id, 'Dorftyp', 'off')

        with open(self.settingpath, 'wb') as cfile:
            self.config.write(cfile)

    def generate_description(self):
        """
        a function to a add a little bit of
        description to wsettings.ini
        """

        self.config.add_section('description')

        self.config.set('description', '# Hier können individuelle Einstellungen zu einzelnen Dörfern gesetzt werden.')
        self.config.set('description', '# Die Settings in settings/settings.ini/control sind immernoch relevant.')
        self.config.set('description', '# Diese werden quasi als globale Settings verwendet.')

        with open(self.settingpath, 'wb') as cfile:
            self.config.write(cfile)




