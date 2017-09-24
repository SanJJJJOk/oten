#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.error import TimedOut
from telegram import ChatAction
from threading import Thread
from oten_core import Oten
import logging
import config
import time
import datetime

#import queue

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO) #filename='logfile.log')
logger = logging.getLogger(__name__)

oten = Oten()
access_user_list = {64798180,}
access_chat_list = {64798180,}


def decor_log(method):
    '''Just log it'''
    def logging_f(*args, **kwargs):
        #args = bot, update
        logger.info('IN: ChatID:%d UserID:%d User:"%s" Message:"%s"' %(
                    args[1].message.chat_id,
                    args[1].message.from_user.id,
                    args[1].message.from_user.username,
                    args[1].message.text))
        return method(*args, **kwargs)
    return logging_f


def access_user(method):
    ''' Check user access'''
    def logging_access_f(*args, **kwargs):
        #args = bot, update
        if args[1].message.from_user.id in access_user_list:
            return method(*args, **kwargs)
        else:
            args[0].sendMessage(args[1].message.chat_id, text="Deny access")
    return logging_access_f


def access_chat(method):
    ''' Check chat access'''
    def logging_access_f(*args, **kwargs):
        if args[1].message.chat_id in access_chat_list:
            return method(*args, **kwargs)
        else:
            args[0].sendMessage(args[1].message.chat_id, text="Deny access")
    return logging_access_f


#Demon for permoment parsing engine
@run_async
def get_page_demon(bot, chat_id):
    '''-'''
    logger.info('Demon Start')
    #While game in active
    while oten.ingame is True:
        time.sleep(2) # wait 2 sec
        #bot.send_message(chat_id=chat_id, text='.')
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        page_res = oten.req.get_page() # Get page
        #if get_page is success
        if page_res is True:
            new_lvl = oten.check_lvl()
            if new_lvl:
                #If new level say it
                bot.send_message(chat_id=chat_id, 
                            text='❗ #АП Уровень:{0}'.format(oten.lastlvl),
                            parse_mode='markdown')
                            
                mess, img_list = oten.new_lvl()
                
                bot.send_message(chat_id=chat_id, 
                            text=mess,
                            parse_mode='markdown',
                            disable_web_page_preview=True)
                if img_list:
                    for img in img_list:
                        bot.send_message(chat_id=chat_id, 
                                text=img,
                                parse_mode='markdown')
            
            #Check update
            else:
                is_update = oten.chack_update()
                if is_update:
                    send_stream_mess(bot, chat_id, is_update)

        elif page_res is False:
            #If need login again
            logger.info('Need relogin')
            oten.login_en()
        else:
            #if network error
            bot.send_message(chat_id=chat_id, text='Ошибка: {}'.format(page_res))
    logger.info('Demon Stop')


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
#@access_user
@decor_log
def start(bot, update):
    '''starting func'''
    update.message.reply_text('Hi!')


@decor_log
@access_chat
def help(bot, update):
    update.message.reply_text(config.HELP)
    

@decor_log
@access_user
def status(bot, update):
    update.message.reply_text('ChatId:{} \nUserId:{}\n\n ChatList:{}\n UserList{}'.format(
                                    update.message.chat_id,
                                    update.message.from_user.id,
                                    access_chat_list,
                                    access_user_list))


@decor_log
@access_user
def gameurl(bot, update, args):
    '''-'''
    try:
        str_in = args[0]
    except IndexError:
        str_in = None

    if str_in:
        done = oten.args_from_url(str_in)
        if done is None:
            update.message.reply_text('Не корректная ссылка')
        else:
            update.message.reply_text('Url принята')
    else:
        update.message.reply_text('Ссылка на игру: {}'.format( oten.generation_url() ))


@decor_log
@access_user
def gamelogin(bot, update):
    '''-'''
    oten.login = update.message.text.split(None, 1)[1]
    update.message.reply_text('Login принят')


@decor_log
@access_user
def gamepas(bot, update):
    '''-'''
    oten.passw = update.message.text.split(None, 1)[1]
    update.message.reply_text('Password принят')


@decor_log
@access_user
def gamestart(bot, update):
    '''-'''
    done = oten.login_en()
    if done is True:
        update.message.reply_text('LogIN - Успешный')
        oten.ingame = True
        access_chat_list.add(update.message.chat_id)
        get_page_demon(bot, update.message.chat_id)
    if done is False:
        update.message.reply_text('Login или Password не верный')
    if done is None:
        update.message.reply_text('Необходимы Login или Password')


@decor_log
@access_user
def gamestop(bot, update):
        oten.ingame = False
        update.message.reply_text('Игра остановлена')


@decor_log
@access_chat
def task(bot, update):
    '''
    Get task from lvl
    Return 2 message:
        1) Text and Name_img with save structur html
        2) Set of images
    '''

    result = oten.get_lvl_body()
    update.message.reply_text(result[0], parse_mode='markdown',disable_web_page_preview=True)

    #Try send Images
    if len(result) > 1:
        for item in result[1]:
            update.message.reply_text(item, parse_mode='markdown')


@decor_log
@access_chat
def raw(bot, update):
    '''
    Get task from lvl
    Return 2 message:
        1) Text and Name_img with save structur html
        2) Set of images
    '''
    result = oten.get_raw_page()
    update.message.reply_text(result[0],disable_web_page_preview=True)

    #Try send Images
    if len(result) > 1:
        for item in result[1]:
            update.message.reply_text(item, parse_mode='markdown')


@decor_log
@access_chat
def hint(bot, update, args):
    '''
    Get task from lvl
    Return 2 message:
        1) Text and Name_img with save structur html
        2) Set of images
    '''
    #try  get arguments from message
    try:
        str_in = args[0]
        #Try get hint of number or last
        #result = oten.get_helps(number=str_in)
        result = oten.get_helps(args[0])
        if result:
            send_stream_mess(bot, update.message.chat_id, result)
        else:
            update.message.reply_text(('Не возможно вывести подсказку',))

    except IndexError:
        result = oten.get_helps()
        if result:
            send_stream_mess(bot, update.message.chat_id, result)
        else:
            update.message.reply_text(('Не возможно вывести подсказки',))


def send_stream_mess(bot, chat_id, stream_mess):
    '''
    Send all messages from  list of massages

    Input:
        - Bot 
        - Update from Telegram Bot Api
        - Stream of messages ( [ [str, [img_urls] ], [str, [img_urls]], ... ] ) 
    '''

    #chat_id = update.message.chat_id
    if stream_mess:
        for mess in stream_mess:
            #update.message.reply_text(mess[0], parse_mode='markdown', disable_web_page_preview=True)
            bot.send_message(chat_id=chat_id, 
                                text=mess[0],
                                parse_mode='markdown',
                                disable_web_page_preview=True)
            try:
                for img in mess[1]:
                    #update.message.reply_text(mess[1], parse_mode='markdown')
                    bot.send_message(chat_id=chat_id, 
                                text=img,
                                parse_mode='markdown')
            except IndexError:
                pass
    else:
        bot.send_message(chat_id=chat_id, 
                                text='INFO: Это пустое сообщение',
                                parse_mode='markdown')


@decor_log
@access_chat
def sect(bot, update):
    '''-'''
    result = oten.get_sectors()
    count_sect = oten.count_sectors()
    if result:
        sect_header = '_Осталось _*{0}*_ из {1}_\n'.format(count_sect[1],count_sect[0])
        update.message.reply_text(sect_header + '*Сектора:*\n' + '\n'.join(result), parse_mode='markdown')
    else:
        update.message.reply_text('На уровне 1 секторов')


@decor_log
@access_chat
def sect_lef(bot, update):
    '''-'''
    result = oten.get_sectors(filt=False)
    count_sect = oten.count_sectors()
    if result:
        sect_header = '_Осталось _*{0}*_ из {1}_\n'.format(count_sect[1],count_sect[0])
        update.message.reply_text(sect_header + '*Сектора:*\n' + '\n'.join(result), parse_mode='markdown')
    else:
        update.message.reply_text('На уровне 1 секторов')


@decor_log
@access_chat
def time_left(bot, update):
    '''-'''
    result = oten.time_left()
    if result:
        update.message.reply_text(result)
    else:
        update.message.reply_text('Ни каких временых рамок нет')


@decor_log
@access_chat
def set_monitor_bonus(bot, update):
    '''-'''
    result = oten.set_monitor_bonus()
    if result:
        update.message.reply_text(result)
    else:
        update.message.reply_text('Данная настройка отсутствует')


@decor_log
@access_chat
def auth_mess(bot, update):
    '''-'''
    result = oten.get_global_mess()
    if result:
        update.message.reply_text(result)
    else:
        update.message.reply_text('Сообщений от авторов нет')


@decor_log
@access_chat
def bonus(bot, update):
    '''-'''
    result = oten.get_bonus_list()
    send_stream_mess(bot, update.message.chat_id, result)


def code(bot, update):
    '''-'''
    if update.message.chat_id in access_chat_list and update.message.text.startswith('.'):
        logger.info('IN: ChatID:%d UserID:%d User:"%s" Message:"%s"' %(
                    update.message.chat_id,
                    update.message.from_user.id,
                    update.message.from_user.username,
                    update.message.text))

        result = oten.check_answer(update.message.text)
        update.message.reply_text(result, parse_mode='markdown')
    

def error(bot, update, error):
    '''-'''
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(config.TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("status", status))

    dp.add_handler(CommandHandler("gameurl", gameurl, pass_args=True))
    dp.add_handler(CommandHandler("gamelogin", gamelogin))
    dp.add_handler(CommandHandler("gamepas", gamepas))
    dp.add_handler(CommandHandler("gamestart", gamestart))
    dp.add_handler(CommandHandler("gamestop", gamestop))

    #dp.add_handler(CommandHandler("connect", connect_chat))
    #dp.add_handler(CommandHandler("disconnect", disconnect_chat))

    dp.add_handler(CommandHandler("task", task))
    dp.add_handler(CommandHandler("sect", sect))
    dp.add_handler(CommandHandler("sectleft", sect_lef))
    
    dp.add_handler(CommandHandler("time", time_left))
    dp.add_handler(CommandHandler("hint", hint, pass_args=True))
    dp.add_handler(CommandHandler("bonus", bonus))

    dp.add_handler(CommandHandler("raw", raw))
    dp.add_handler(CommandHandler("mes", auth_mess))

    dp.add_handler(CommandHandler("set_mon", set_monitor_bonus))
    
    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, code))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    logger.info('Bot started')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



if __name__ == '__main__':
    main()