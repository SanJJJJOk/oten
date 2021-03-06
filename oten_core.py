#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import lxml
import csv
import re
import logging
import csv
import request
from deepdiff import DeepDiff
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
        
        self.storm = None
        self.lastlvl = 0
        self.correct_lvl = False
        self.answer_block = False
        self.help_close = 0
        self.help_open = 0
        self.bonus_dict = dict()
        self.auth_mess = ''

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


    def set_url_lvl(self, level = None):
        '''Set url for storm game mode'''
        
        if level is not None and self.storm is not None:
            if 0 < int(level) <= self.storm:
                self.req.url = self.generation_url(level)
                return True
            else:
                return False
        else:
            return False


    def generation_url(self, level=None):
        '''Return URL for game'''
        
        if level is None:
            return 'http://{0}.en.cx/gameengines/encounter/play/{1}'.format(self.domain, self.gid)
        else:
            return 'http://{0}.en.cx/gameengines/encounter/play/{1}/?level={2}'.format(
                                                        self.domain, self.gid, level)


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
        return self.req.get_raw_page(correct_lvl=self.correct_lvl)


    def get_task(self):
        """
        Get full block with name

        Return:
            list:
                1: Text block (str) - Text with markdown
                2: Imgs list (tuple)
        
        If there is't block return None
        """
        task_unit = self.req.get_unit(header='Задание')
        task_text = '*Задание:*\n{}'.format(task_unit[0])

        return task_text, task_unit[1]


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
                hint_unit = self.req.get_unit(header=header)
                if hint_unit is not None:
                    hint_text = '❓*{0}:*\n{1}'.format(header, hint_unit[0])
                    result.append([hint_text, hint_unit[1]])
        else:
            #generate hint stream for selected hint
            header = 'Подсказка {0}'.format(number)
            hint_unit = self.req.get_unit(header=header)
            if hint_unit is not None:
                hint_text = '❓*{0}:*\n{1}'.format(header, hint_unit[0])
                result.append([hint_text, hint_unit[1]])
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
            result += 'Авто Переход через {0}\n'.format(time_up[0])
        if time_hint:
            result += '\nПодсказки будут через:\n'
            for time_str in time_hint[0]:
                result += '{0}\n'.format(time_str)
        if result is not '':
            return result
        else:
            return 'На уровне нет таймеров\n'


    def check_lvl(self):
        '''
        Check New lvl
        If New LVL return True
        else False
        '''
        current_lvl = self.req.get_lvl()
        if current_lvl != self.lastlvl:
            if current_lvl != 0:
                self.lastlvl = current_lvl
                self.correct_lvl = True
                return True
            else:
                #Если появилось какое-то сообщение
                if self.correct_lvl == True:
                    self.correct_lvl = False
                    return True
                else:
                    return False
        else:
            return False


    def check_answer(self, answer=''):
        '''
        Input:
            type: True - Level Answer
                False - Bonus Answer
        '''
        if self.ingame:
            #If theris block answer
            if self.answer_block:

                #Send to answer form
                if answer.startswith('..'):
                    result = self.req.send_answer(answer=answer[2:])
                    count_sect = self.count_sectors()
                    if result is True:
                        return '✅ Код верный.\n(осталось {0} из {1})'.format(
                                                count_sect[1],count_sect[0])
                    elif result is False:
                        return '❌ Код НЕ верный.\n(осталось {0} из {1})'.format(
                                                count_sect[1],count_sect[0])
                
                #Send to bonus form
                else:
                    result = self.req.send_answer(answer=answer[1:], type=False)
                    if result is True:
                        return '✅ Бонус верный.\n\n_Для отправки в ответы необходимо_".."'
                    elif result is False:
                        return '❌ Бонус НЕ верный.\n\n_Для отправки в ответы необходимо_".."'
                
            #If there is't block
            else:
                result = self.req.send_answer(answer=answer[1:])
                count_sect = self.count_sectors()
                if result is True:
                    return '✅ Код верный.\n(осталось {0} из {1})'.format(
                                            count_sect[1],count_sect[0])
                elif result is False:
                    return '❌ Код НЕ верный.\n(осталось {0} из {1})'.format(
                                            count_sect[1],count_sect[0])


    def check_update(self):
        '''
        Check all update at LVL and generation mess stream
        
        Return:
            Tuple - [ [str], [str,[img_tuple]], [str,[img_tuple]] ]
        '''
        update_list = []

        new_help = self.check_helps()
        if new_help:
            update_list.extend(self.get_helps(self.help_open))

        new_mess = self.req.get_global_mess()
        if new_mess and self.auth_mess != new_mess:
            self.auth_mess = new_mess
            author_mess_head = '✉ Новое сообщение от авторов:\n{}'.format(new_mess)
            update_list.append([author_mess_head])

        if self.st_monitor_bonus != 0:
            new_bonus = self.check_bonus()
            if new_bonus:
                update_list.extend(new_bonus)

        return update_list.copy()


    def set_monitor_bonus(self):
        '''
        Switch monitor setting
        '''
        if self.st_monitor_bonus == 0:
            self.st_monitor_bonus = 1
        else:
            self.st_monitor_bonus = 0
        return 'Статус мониторинга - {0}'.format(self.st_monitor_bonus)


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
        self.answer_block = False
        self.help_close = 0
        self.help_open = 0
        self.bonus_dict.clear()

        answer_block = self.req.check_answer_block()
        if answer_block:
            self.answer_block = True

        return self.get_lvl_body()


    def get_lvl_body(self):
        '''
        Get main information about lvl
        '''
        result = ''
        title = self.req.get_lvl_title()
        timer = self.time_left()

        fine_hint = self.req.check_fine_hints()
        logger.info(fine_hint)
        if fine_hint is not None:
            fine_hint_text = '_На уровне штрафные подсказки {0}ш._\n'.format(fine_hint)
        else:
            fine_hint_text = ''
        
        sect_count = self.req.get_sectors_title()
        sect_title = 'Нужно закрыть: {} из {}'.format(sect_count[1],sect_count[0])

        task = self.get_task()
        
        result = '*{0}*\n{1}\n{2}{3}\n{4}'.format(title, sect_title, timer, fine_hint_text, task[0])
        return result,task[1]


    def get_bonus_list(self):
        bonus_list = self.req.get_bonus_list()
        
        result = []
        if bonus_list is not None:
            
            #1: list available bonus
            #2: list completed bonus
            #3: list future bonus
            
            #Retern body bonus
            '''
            for bonus in bonus_list:
                result.append(self.req.get_unit(header=bonus, 
                                                offset=0))
            '''
            
            #Return title bonus
            #print (bonus_list)
            
            #available
            bonus_list_str = '\n'.join(bonus_list[0])
            mes = "*Бонусы* (осталовь %d):\n" %len(bonus_list[0]) + bonus_list_str
            result.append([mes,])

            #completed
            seconds = 0

            for bonus in bonus_list[1]:
                #print(bonus)
                try:
                    hour = re.search('\d час', bonus).group(0)
                    seconds += int(hour.split(' ')[0])*3600
                    #print(hour)
                except AttributeError:
                    pass

                try:
                    minut = re.search('\d мину', bonus).group(0)
                    seconds += int(minut.split(' ')[0])*60
                    #print(minut)
                except AttributeError:
                    pass
                
                try:
                    second = re.search('\d секун', bonus).group(0)
                    seconds += int(second.split(' ')[0])
                    #print(second)
                except AttributeError:
                    pass


            bonus_list_str = '\n'.join(bonus_list[1])
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            mes = "*Закрытые* (%d:%02d:%02d):\n" % (h, m, s) + bonus_list_str
            result.append([mes,])

            #available
            bonus_list_str = '\n'.join(bonus_list[2])
            mes = "*Будущие*:\n" + bonus_list_str
            result.append([mes,])

        else:
            result.append( ('На уровне бонусов нет',) )
        return result

    def check_bonus(self):
        '''
        Check open new help or not

        1 - open ponus
        2 - completle bonus
        3 - close bonus

        '''
        
        #Create list of bonus
        bonus_list = self.req.get_bonus_dict()
        
        if (bonus_list is not None) and (self.bonus_dict != bonus_list):

            result = []    
            #Compare old and new bonus lists
            ddiff = DeepDiff(self.bonus_dict, bonus_list)
            
            #logger.info(ddiff)

            #For each new bonus

            #values_changed
            try:
                for element in ddiff["values_changed"]:
                    #If bonus completle
                    if ddiff["values_changed"][element]['new_value'] == 2:
                        result.append(self.req.get_unit(
                                            header=element.split("'")[1], 
                                            offset=0,
                                            icon = '✅ ')
                        )
                    #If bonus open
                    elif ddiff["values_changed"][element]['new_value'] == 1:
                        result.append(self.req.get_unit(
                                            header=element.split("'")[1], 
                                            offset=0,
                                            icon = '❎ ')
                        )
            except KeyError:
                pass

            #dictionary_item_added
            try:
                for element in ddiff["dictionary_item_added"]:
                    #If bonus completle
                    if bonus_list[element.split("'")[1]] == 2:
                        result.append(self.req.get_unit(
                                            header=element.split("'")[1], 
                                            offset=0,
                                            icon = '✅ ')
                        )
                    #If bonus open
                    elif bonus_list[element.split("'")[1]] == 1:
                        result.append(self.req.get_unit(
                                            header=element.split("'")[1], 
                                            offset=0,
                                            icon = '❎ ')
                        )
            except KeyError:
                pass
            
            self.bonus_dict = bonus_list
            #logger.info(result)
            return result
        else:
            return None


    def get_global_mess(self):
        author_mess_head = '✉ Сообщение от авторов:\n'
        return author_mess_head + self.req.get_global_mess()


    def update_storm(self):
        self.storm = self.req.check_shtorm()


def main():
    pass


if __name__ == '__main__':
    main()
