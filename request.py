#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import requests
import logging
import time
from lxml import html, etree


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

class Request(object):
    '''
    Class for handling requests from site
    '''
    def __init__(self, url = None):
        self.url = url
        self.page = None
        self.session = requests.session()

        self.session.headers.update({
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
            'User-Agent': 'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',
            'Connection':'keep-alive'})


    def _request_wrapper(self, resp=None):
        """Wraps Requests request for handling known exceptions."""

        if resp is not None:
            if 'login.aspx' in resp.url:
                logger.info('Необходимо авторизироваться: {}'.format(resp.url))
                return False
            elif 200 <= resp.status_code <= 299:
                parser = html.HTMLParser(encoding='utf-8')
                page = html.fromstring(resp.content, parser=parser)
                self.page = page
                return True
            else:
                logger.info('Не удалось загрузить страницу')
                return resp.status_cod


    def get_page(self, url=None):
        '''-'''
        if url is None:
            url = self.url
        resp = self.session.get(url)
        return self._request_wrapper(resp)


    def check_login(self, domain):
        '''-'''
        url = 'http://{0}.en.cx/UserDetails.aspx'.format(domain)
        resp = self.session.get(url)
        if resp.url == url:
            return True
        else:
            return False


    def send_answer(self, url=None, answer=''):
        if url is None:
            url = self.url

        last_data = self.page.xpath('//input[@type="hidden"]/@value')
        userdata = {
            'LevelId': last_data[0],
            'LevelNumber': last_data[1],
            'LevelAction.Answer': answer
            }

        resp = self.session.post(url, data=userdata)
        result = self._request_wrapper(resp)
        if result:
            text_answer = self.page.xpath('//*[@class="history"]/li[1]/text()')[0]
            logger.info(text_answer)
            if 'код верный' in text_answer:
                return True
            else:
                return False


    def login_en(self, domain=None, login=None, password=None):
        """
        Method login on encounter website
        """
        if (domain is not None) and\
             (login is not None) and\
             (password is not None):

            url = 'http://{0}.en.cx/Login.aspx?return=%%2f'.format(domain)
            userdata = {
                'socialAssign': 0,
                'Login': login,
                'Password': password,
                'EnButton1': 'Вход',
                'ddlNetwork': 1
            }

            resp = self.session.get(url)
            resp = self.session.post(url, data=userdata)

            #Check LogIN
            #Данный код основывается на том что при авторизации
            #у нас будет переадресация на главную старницу
            if resp.history:
                logger.info("LogIN")
                return True
            else:
                logger.info("LogOUT")
                return False
        else:
            logger.info('Bad args for login')
            return None


    def clear_string(self, str_in):
        '''Удаление \t и \n'''
        str_out = str_in.replace('\t', '')
        str_out = str_in.replace('\r', '\n')
        str_out = str_in.replace('\n\n', '\n')
        str_out = str_out.strip()
        return str_out


    def get_lvl(self, page=None):
        '''
        Function get current Level Number
        Result:
            lvl(int) - level number
        '''
        if page is None:
            page = self.page
        
        if page is not None:
            try:
                lvl = page.xpath('//*[@name="LevelNumber"]/@value')[0]
                return int(lvl)
            except IndexError:
                return None


    def get_lvl_title(self, page=None):
        '''
        Function get current Level Number
        Result:
            lvl_title(str)
        '''
        if page is None:
            page = self.page
        
        if page is not None:
            lvl_title = page.xpath('//h2')[0]
            return lvl_title.text_content()


    def check_ap(self, page=None):
        '''-'''
        if page is None:
            page = self.page
        ap = page.xpath('//h3[@class="timer"]/span/text()')
        if ap:
            return ap
        else:
            return None


    def check_help(self, page=None):
        '''
        Find and count helps on lvl

        Returns:
            tuple of list:
                1: list time of close helps
                2: list time of opened helps
        '''
        if page is None:
            page = self.page

        helps_close = page.xpath('//span[@class="color_dis" and starts-with(., "Подсказка")]/span/text()')
        helps_open = page.xpath('//h3[starts-with(., "Подсказка")]/text()')

        if helps_close or helps_open:
            return helps_close, helps_open
        else:
            return None


    def get_sectors_title(self, page=None):
        """
        Get information about sectors from en
        
        Result:
            tuple:
                1: Total number of sectors
                2: Number of sectors to be closed
        """
        if page is None:
            page = self.page
        
        sector_title_1 = page.xpath('//h3[starts-with(., "На уровне")]/text()')[0]
        print(sector_title_1)
        total = sector_title_1.split(' ')[2]

        try:        
            sector_title_1 = page.xpath('//h3[starts-with(., "На уровне")]/span/text()')[0]
            need = sector_title_1.split(' ')[2][:-1]
        except IndexError:
            need = total
        return(total, need)



    def get_sectors(self, page=None, filt=None):
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
        if page is None:
            page = self.page
        result = []

        sectors = page.xpath('//div[@class="cols w100per"]/p')

        #Return All
        if filt is None:
            for sector in sectors:
                result.append(sector.text_content())
        elif filt is False:
            #Return Left
            for sector in sectors:
                if not sector.xpath('./span[@class="color_correct"]'):
                    result.append(sector.text[:-2])
        elif filt is True:
            #Return Done
            for sector in sectors:
                if sector.xpath('./span[@class="color_correct"]'):
                    result.append(sector.text_content())
        return result.copy()


    def get_block(self, page=None, header='Задание'):
        '''
        Get full block with name

        Return:
            list:
                1: Text block (str)
                2: Imgs list (tuple)
        
        If there is't block return None
        '''

        if page is None:
            page = self.page
        end = None
        
        #Get parent for index element
        cont = page.xpath('//div[@class="content"]')[0]

        #Get start point
        try:
            start = cont.index(cont.xpath('//h3[text()="%s"]' %header)[0])+1
        except IndexError:
            start = None
        
        if start is not None:
            #Try get end point.
            try:
                space_list = cont.xpath('//div[@class="spacer"]')
                index_list = list(cont.index(x) for x in space_list if cont.index(x) > start)
                end = index_list[0]
            except IndexError:
                pass

            #Fix <br> tags
            for br_tag in cont.xpath("*//br"):
                br_tag.tail = "\n" + br_tag.tail if br_tag.tail else "\n"

            text_block = []
            imgs_block = set()

            #Foreach element between tags
            for item in cont[start:end]:
                #headling image
                img_list, item = self.handling_img_block(item)
                imgs_block.update(img_list)
                #headling text
                text_block.append(self.clear_string(item.text_content()))
            
            return("\n".join(text_block),tuple(imgs_block))
        else:
            return None


    def handling_img_block(self, page):
        """
        Replace IMG tags to plain text

        Result:
            img_list (list)
            page (html.doc)
        """
        image_list = set()
        #find all img tags
        for img in page.xpath("./img"):
            #Take url and name
            url = img.get('src')
            name = url[url.rfind('/')+1:]

            #image_list.add(name + ':' + url)
            image_list.add('[{}]({})'.format(name, url))

            newtag = etree.Element("a", href=url)
            #newtag.text = '[' + name + ']'
            newtag.text = '[{}]({})'.format(name, url)

            img.getparent().replace(img,newtag)
        return image_list.copy(), page


    def get_get_img(self, page=None):
        '''
        Get all image

        Return:
            Imgs list (tuple)
        
        If there is't block return None
        '''

        if page is None:
            page = self.page
        end = None
        
        image_list = set()
        #find all img tags
        for img in page.xpath('//div[@class="content"]/img'):
            #Take url and name
            url = img.get('src')
            name = url[url.rfind('/')+1:]
            #image_list.add(name + ':' + url)
            image_list.add('[{}]({})'.format(name, url))
        return tuple(image_list)



def main():
    """-"""
    requ = Request()
    #page = requ.get_page('http://demo.en.cx/gameengines/encounter/play/26971')
    
    page = html.parse('example_page/without_time.html')
    
    print(requ.check_help(page=page))

    #print(requ.get_sectors_title(page=page))
    #print(requ.get_sectors(page=page, filt=None))
    #print(requ.get_sectors(page=page, filt=True))
    #print(requ.get_sectors(page=page, filt=False))



if __name__ == '__main__':
    main()

