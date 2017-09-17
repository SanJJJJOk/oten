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
logger = logging.getLogger(__name__)


class Oten():
    """
    This class provides parsing and handling encounter
    """

    def __init__(self, url_game=None):
        """-"""
        self.domain = None
        self.gid = None
        self.login = None
        self.passw = None
        self.req = Request()
        self.ingame = False
        
        self.lastlvl = 0
        self.help_close = 0
        self.help_open = 0
        self.bonus_dict = {}

        self.st_monitor_bonus = 0


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


    def count_sectors(self):
        '''
        Get Sectors at lvl
        Args:
            page - html page for parsing
            
        Rets:
            List of integer:
            1 - all sectors
            2 - left sectors
        '''
        sect_count = self.req.get_sectors_title()
        return sect_count


    def get_raw_page(self):
        '''
        Get full page text

        Return:
            list:
                1: Text block (str) - Text with markdown
                2: Imgs list (tuple)
        '''

        return self.req.get_raw_page()


    def get_task(self):
        """
        Get full block with name

        Return:
            list:
                1: Text block (str) - Text with markdown
                2: Imgs list (tuple)
        
        If there is't block return None
        """
        task_blocks = self.req.get_block(header='Задание')
        task_text = '*Задание:*\n{}'.format(task_blocks[0])

        return task_text, task_blocks[1]


    def get_helps(self, number=None):
        '''-'''
        result = []

        #Add header for hint blocks
        str_hint_count = 'На уровне {0} подсказок, на данный момент доступно {1}\n'\
                        ''.format(self.help_close + self.help_open, self.help_open)
        result.append([str_hint_count,])

        if number is None:
            #generate hint stream
            for i in range(0, self.help_open):
                number = i+1
                header = 'Подсказка {0}'.format(number)
                hint_blocks = self.req.get_block(header=header)
                hint_text = '❓*{0}:*\n{1}'.format(header, hint_blocks[0])
                result.append([hint_text, hint_blocks[1]])
        else:
            #generate hint stream for selected hint
            header = 'Подсказка {0}'.format(number)
            hint_blocks = self.req.get_block(header=header)
            hint_text = '❓*{0}:*\n{1}'.format(header, hint_blocks[0])
            result.append([hint_text, hint_blocks[1]])
        return result


    def time_left(self):
        """
        Collects and processes timers

        Result:
            Str - ready message
        """
        time_up = self.req.check_ap()
        time_hint = self.req.check_help()
        result = ''

        if time_up:
            result += 'Авто Переход через {0}\n\n'.format(time_up[0])
        if time_hint[0]:
            result += 'Подсказки будут через:\n'
            for time_str in time_hint[0]:
                result += '{0}\n'.format(time_str)
        if result is not '':
            return result
        else:
            return 'На уровне нет таймеров'


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


    def check_helps(self):
        '''
        Check open new help or not
        '''
        helps_list = self.req.check_help()
        if helps_list is not None:
            heco = len(helps_list[0])
            heop = len(helps_list[1])
            if (self.help_close != heco) or (self.help_open != heop):
                self.help_close = heco
                self.help_open = heop
                return True
            else:
                return None
        return None


    def new_lvl(self):
        '''
        Reset setting for new LVL
        '''
        
        #Reset
        self.help_close = 0
        self.help_open = 0
        self.bonus_dict.clear()

        #Update info about hints
        #helps_list = self.req.check_help()
        #self.help_close = len(helps_list[0])
        #self.help_open = len(helps_list[1])

        return self.get_lvl_blocks()


    def get_lvl_blocks(self):
        '''
        Get main information about lvl
        '''
        title = self.req.get_lvl_title()
        timer = self.time_left()
        
        sect_count = self.req.get_sectors_title()
        sect_title = 'Нужно закрыть: {} из {}'.format(sect_count[1],sect_count[0])

        task = self.get_task()
        #logger.info(task)

        result = '*{0}*\n{2}\n{1}\n\n{3}'.format(title, timer, sect_title, task[0])
        return result,task[1]


    def get_bonus_list(self):
        self.bonus_dict = self.req.get_bonus_list()


    def get_global_mess(self):
        return self.req.get_global_mess()


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
    #print(ob_c1.args_from_url('http://demo.en.cx/GameDetails.aspx?gid=26971'))
    #forum
    #print(ob_c1.args_from_url('http://demo.en.cx/gameengines/encounter/play/26971'))
    #game
    #ob_c1.args_from_url('http://demo.en.cx/GameDetails.aspx?gid=26971')

'''
Обработка даты
datetime_object = datetime.strptime(values[-1], '%d.%m.%Y %H:%M:%S.%f')
print(datetime_object.time())
'''



if __name__ == '__main__':
    main()
