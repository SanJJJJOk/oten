#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import lxml
import csv
import re
import logging
import csv
import request
from operator import itemgetter
from request import Request



# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class Oten():
    """
    This class provides parsing and handling encounter
    """

    def __init__(self, url_game=None):
        """-"""
        self.log = logging.getLogger(__name__)
        self.domain = None
        self.gid = None
        self.login = None
        self.passw = None
        self.req = Request()
        self.ingame = False
        
        self.lastlvl = 0

        if url_game is not None:
            self.args_from_url(url_game)


    def get_page(self):
        '''-'''
        if self.req.check_login(self.domain):
            self.req.get_page()


    def args_from_url(self, url_str):
        """
        This metod get DOMAIN(domain) and Game-ID(gid) from URL
        Args:
            url_str - str
        Result:
            tuple(domain,gid)
        """
        #http://demo.en.cx/gameengines/encounter/play/26971
        match = re.search(r'([\w\d]*.en.cx).*(gid=[\d]*)', url_str)
        try:
            self.domain = match.groups()[0].split('.')[0]
            self.gid = match.groups()[1][4:]
            self.req.url = self.generation_url()
            return True
        except AttributeError:
            return None


    def generation_url(self):
        '''Return URL for game'''
        return 'http://{}.en.cx/gameengines/encounter/play/{}'.format(self.domain, self.gid)


    def login_en(self, login=None, password=None):
        '''-'''
        if login is None:
            login = self.login
        if password is None:
            password = self.passw

        done = self.req.login_en(self.domain, login, password)
        return done


    def get_sectors(self, filt=None):
        '''
        Get Sectors at lvl
        Args:
            page - html page for parsing
            filt - filter for sectors:
                None - return ALL
                False - return LEFT
                True - return CLOSED

        Rets:
            List of strig
        '''
        return self.req.get_sectors(filt=filt)


    def get_task(self):
        '''-'''
        return self.req.get_block(header='Задание')


    def check_lvl(self):
        '''
        Check New lvl
        If New LVL return True
        else False
        '''
        current_lvl = self.req.get_lvl()
        if (current_lvl is not None) and (current_lvl != self.lastlvl):
            self.lastlvl = current_lvl
            return True
        else:
            return False


    def check_answer(self, answer=''):
        if self.ingame:
            return self.req.send_answer(answer=answer)
        else:
            return None



def main():
    """-"""
    '''
    ob_c1 = Monitoring('http://72.en.cx/GameDetails.aspx?gid=58789')
    ob_c1.login_en(login='', password='')
    ob_c1.get_monitor()
    #ob_c1.get_stats()
    '''
    ob_c1 = Oten()
    
    #Main
    print(ob_c1.args_from_url('http://demo.en.cx/GameDetails.aspx?gid=26971'))
    #forum
    print(ob_c1.args_from_url('http://demo.en.cx/gameengines/encounter/play/26971'))
    #game
    ob_c1.args_from_url('http://demo.en.cx/GameDetails.aspx?gid=26971')

'''
Обработка даты
datetime_object = datetime.strptime(values[-1], '%d.%m.%Y %H:%M:%S.%f')
print(datetime_object.time())
'''



if __name__ == '__main__':
    main()
