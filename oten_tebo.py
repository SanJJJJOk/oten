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

#update.message.text.split(None, 1)[1]
oten = Oten()
access = {64798180}
#que = Queue.Queue()

def decor_log(method):
    def logging_f(bot, update):
        print('IN: UserID:%d User:"%s" Message:"%s"' %(
                update.message.from_user.id,
                update.message.from_user.username,
                update.message.text))
        return method(bot, update)
    return logging_f


def decor_user_access(method):
    def logging_access_f(bot, update):
        logger.info('IN: ChatID:%d UserID:%d User:"%s" Message:"%s"' %(
                    update.message.chat_id,
                    update.message.from_user.username,
                    update.message.text))
        if update.message.from_user.id in access:
            return method(bot, update)
        else:
            bot.sendMessage(update.message.chat_id, text="Deny access")
    return logging_access_f


def decor_chat_access(method):
    def logging_access_f(bot, update):
        logger.info('IN: ChatID:%d UserID:%d User:"%s" Message:"%s"' %(
                    update.message.chat_id,
                    update.message.from_user.username,
                    update.message.text))
        if update.message.from_user.id in access:
            return method(bot, update)
        else:
            bot.sendMessage(update.message.chat_id, text="Deny access")
    return logging_access_f


def decor_chat_access(method):
    def logging_access_f(bot, update):
        logger.info('IN: ChatID:%d UserID:%d User:"%s" Message:"%s"' %(
                    update.message.chat_id,
                    update.message.from_user.id,
                    update.message.from_user.username,
                    update.message.text))
        if update.message.chat_id in access:
            return method(bot, update)
        else:
            bot.sendMessage(update.message.chat_id, text="Deny access")
    return logging_access_f


#Demon for permoment parsing engine
@run_async
def get_page_demon(bot, chat_id):
    '''-'''
    logger.info('Demon Start')
    #While game in active
    while oten.ingame is True:
        time.sleep(2) # wait 2 sec
        bot.send_message(chat_id=chat_id, text='.')
        page_res = oten.req.get_page() # Get page
        #if get_page is success
        if page_res is True:
            new_lvl = oten.check_lvl()
            if new_lvl:
                #If new level say it
                bot.send_message(chat_id=chat_id, text='#АП Уровень:{}'.format(oten.lastlvl))
        elif page_res is False:
            #If need login again
            oten.login_en()
        else:
            #if network error
            bot.send_message(chat_id=chat_id, text='Ошибка: {}'.format(page_res))
    logger.info('Demon Stop')


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    '''starting func'''
    update.message.reply_text('Hi!')


def help(bot, update):
    update.message.reply_text('Help!')


def status(bot, update):
    update.message.reply_text('ChatId:{} \nUserId:{}'.format(
                                    update.message.chat_id,
                                    update.message.from_user.id))


def gameurl(bot, update):
    '''-'''
    try:
        str_in = update.message.text.split(None, 1)[1]
    except:
        pass

    if str_in:
        done = oten.args_from_url(str_in)
        if done is None:
            update.message.reply_text('Не корректная ссылка')
        else:
            update.message.reply_text('Url принята')
    else:
        update.message.reply_text('Ссылка на игру: {}'.format( oten.generation_url() ))


def gamelogin(bot, update):
    '''-'''
    oten.login = update.message.text.split(None, 1)[1]
    update.message.reply_text('Login принят')


def gamepas(bot, update):
    '''-'''
    oten.passw = update.message.text.split(None, 1)[1]
    update.message.reply_text('Password принят')


def gamestart(bot, update):
    '''-'''
    done = oten.login_en()
    if done is True:
        update.message.reply_text('LogIN - Успешный')
        oten.ingame = True
        get_page_demon(bot, update.message.chat_id)
    if done is False:
        update.message.reply_text('Login или Password не верный')
    if done is None:
        update.message.reply_text('Необходимы Login или Password')


def gamestop(bot, update):
        oten.ingame = False
        update.message.reply_text('Игра остановлена')


def task(bot, update):
    '''
    Get task from lvl
    Return 2 message:
        1) Text and Name_img with save structur html
        2) Set of images
    '''
    result = oten.get_task()
    update.message.reply_text('Задание:\n' + result[0])
    
    #Try send Images
    if len(result) > 1:
        update.message.reply_text('\n'.join(result[1]))


def sect(bot, update):
    '''-'''
    result = oten.get_sectors()
    if result:
        update.message.reply_text('Сектора:\n' + '\n'.join(result))
    else:
        update.message.reply_text('На уровне 1 секторов')


def sect_lef(bot, update):
    '''-'''
    result = oten.get_sectors(filt=False)
    if result:
        update.message.reply_text('Сектора:\n' + '\n'.join(result))
    else:
        update.message.reply_text('На уровне 1 секторов')


def time_f(bot, update):
    '''-'''
    update.message.reply_text('')


def hint(bot, update):
    '''-'''
    update.message.reply_text('')


def bonus(bot, update):
    '''-'''
    update.message.reply_text('')


def code(bot, update):
    '''-'''
    if update.message.text.startswith('.'):
        result = oten.check_answer(update.message.text[1:])
        if result is True:
            update.message.reply_text('+')
        elif result is False:
            update.message.reply_text('-')
        else:
            pass

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

    dp.add_handler(CommandHandler("gameurl", gameurl))
    dp.add_handler(CommandHandler("gamelogin", gamelogin))
    dp.add_handler(CommandHandler("gamepas", gamepas))
    dp.add_handler(CommandHandler("gamestart", gamestart))
    dp.add_handler(CommandHandler("gamestop", gamestop))

    dp.add_handler(CommandHandler("task", task))
    dp.add_handler(CommandHandler("sect", sect))
    dp.add_handler(CommandHandler("sectlef", sect_lef))
    
    dp.add_handler(CommandHandler("time", time_f))
    dp.add_handler(CommandHandler("hint", hint))
    dp.add_handler(CommandHandler("bonus", bonus))


    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, code))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()