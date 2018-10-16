#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import module
import json
import pickle
import time

# New method for create multiple and different scripts
from scripts import scripts
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# Telegram imports
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
# Thread class in another file
from thread import Thread
from utils import *

# Load settings
with open('settings.json') as f:
    settings = json.load(f)

telegram_token = settings['telegram_token']
allowed_id = settings['allowed_id']
user = {'username': settings['insta_user'], 'password': settings['insta_pass'], 'proxy': None}

# Create array with all threads
threads = {}


def help(bot, update):
    update.message.reply_text('Hi! Use /set to start the bot')


def now(bot, update, args):
    if str(update.message.chat_id) in allowed_id:
        try:

            if not args[0] in scripts:
                update.message.reply_text("Sorry, script named <b>{}</b> is not in your scripts file.".format(args[0]),
                                          parse_mode='HTML')
                return

            job_name = "{}_temp_{}".format(args[0], time.time())
            temp_thread = Thread(
                job_name,
                args[0],
                update.message.chat_id,
                bot,
                user['username'],
                user['password'],
                user['proxy']
            )
            temp_thread.start()
        except (IndexError, ValueError):
            update.message.reply_text('Usage: /now <script_name>')
    else:
        message = 'You have not the permission to use this bot.\nFor more details visit [Telegram-InstaPy-Scheduling](https://github.com/Tkd-Alex/Telegram-InstaPy-Scheduling)'
        update.message.reply_text(message, parse_mode='Markdown')


def exec_thread(bot, job):
    if threads[job.name].isAlive():
        bot.send_message(threads[job.name].chat_id, text="Sorry <b>{}</b> already executing!".format(job.name),
                         parse_mode='HTML')
    else:
        threads[job.name] = reload_thread(threads[job.name])
        threads[job.name].start()


def create_thread(bot, context):
    threads[context['job_name']] = Thread(
        context['job_name'],
        context['script_name'],
        context['chat_id'],
        bot,
        context['user']['username'],
        context['user']['password'],
        context['user']['proxy']
    )


def status_thread(bot, update, args):
    if str(update.message.chat_id) in allowed_id:
        if len(args) != 0:
            message = ""
            for arg in args:
                if arg in threads:
                    message += "\n<b>Name:</b> {} <b>Account:</b> {} <b>Script:</b> {} <b>Status:</b> {}".format(
                        arg, threads[arg].username, threads[arg].script_name, "ON" if threads[arg].isAlive() else "OFF"
                    )
                else:
                    message += "\n<b>Name:</b> {} not found in thread lists.".format(arg)
        else:
            message = "There are {} threads configured.".format(len(threads))
            index = 1
            for thread in threads:
                message += "\n{}) <b>Name:</b> {} <b>Account:</b> {} <b>Script:</b> {} <b>Status:</b> {}".format(
                    index, thread, threads[thread].username, threads[thread].script_name,
                    "ON" if threads[thread].isAlive() else "OFF"
                )
                index += 1

        update.message.reply_text(message, parse_mode='HTML')
    else:
        message = 'You have not the permission to use this bot.\nFor more details visit [Telegram-InstaPy-Scheduling](https://github.com/Tkd-Alex/Telegram-InstaPy-Scheduling)'
        update.message.reply_text(message, parse_mode='Markdown')


def set(bot, update, args, job_queue, chat_data):
    if str(update.message.chat_id) in allowed_id:
        try:
            if args[0] in chat_data or args[1] in threads:
                update.message.reply_text("Sorry, job named <b>{}</b> is already used.".format(args[0]),
                                          parse_mode='HTML')
                return

            if not args[1] in scripts:
                update.message.reply_text("Sorry, script named <b>{}</b> is not in your scripts file.".format(args[1]),
                                          parse_mode='HTML')
                return

            data = {
                'username': user['username'],
                'job_name': args[0],
                'script_name': args[1],
                'scheduled': args[2],
                'days': []
            }
            chat_data['tmpjob'] = data

            keyboard = [[InlineKeyboardButton("Sunday", callback_data='6'),
                         InlineKeyboardButton("Monday", callback_data='0'),
                         InlineKeyboardButton("Tuesday", callback_data='1'),
                         InlineKeyboardButton("Wednesday", callback_data='2')],
                        [InlineKeyboardButton("Thursday", callback_data='3'),
                         InlineKeyboardButton("Friday", callback_data='4'),
                         InlineKeyboardButton("Saturday", callback_data='5')],
                        [InlineKeyboardButton("Everyday", callback_data='-1')]]

            update.message.reply_text('Choose a day: ', reply_markup=InlineKeyboardMarkup(keyboard))
        except (IndexError, ValueError):
            update.message.reply_text('Usage: /set <username> <job_name> <script_name> <hh:mm:ss>')

    else:
        message = 'You have not the permission to use this bot.\nFor more details visit [Telegram-InstaPy-Scheduling](https://github.com/Tkd-Alex/Telegram-InstaPy-Scheduling)'
        update.message.reply_text(message, parse_mode='Markdown')


def day_choose(bot, update, job_queue, chat_data):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    query = update.callback_query

    scheduled_time = parse_time(chat_data['tmpjob']['scheduled'])
    name_job = chat_data['tmpjob']['job_name']

    if query.data == '-1' or query.data == '-2':
        context = {
            "job_name": chat_data['tmpjob']['job_name'],
            "script_name": chat_data['tmpjob']['script_name'],
            "user": user,
            "chat_id": query.message.chat_id,
        }

        create_thread(bot, context)

        if query.data == '-1':
            job = job_queue.run_daily(exec_thread, scheduled_time, context=context, name=name_job)
        else:
            selected_days = ", ".join([days[i] for i in chat_data['tmpjob']['days']])
            job = job_queue.run_daily(exec_thread, scheduled_time, days=tuple(chat_data['tmpjob']['days']),
                                      context=context, name=name_job)

        data = {
            'name': name_job,
            "script_name": chat_data['tmpjob']['script_name'],
            'scheduled': chat_data['tmpjob']['scheduled'],
            "username": chat_data['tmpjob']['username'],
            'job': job,
            'days': "Everyday" if query.data == '-1' else selected_days
        }
        chat_data[name_job] = data
        del chat_data['tmpjob']

        bot.edit_message_text(text="Job <b>{}</b> setted!".format(name_job), chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='HTML')
    else:
        if int(query.data) not in chat_data['tmpjob']['days']:
            chat_data['tmpjob']['days'].append(int(query.data))

        keyboard = [[InlineKeyboardButton("Sunday", callback_data='6'),
                     InlineKeyboardButton("Monday", callback_data='0'),
                     InlineKeyboardButton("Tuesday", callback_data='1'),
                     InlineKeyboardButton("Wednesday", callback_data='2')],
                    [InlineKeyboardButton("Thursday", callback_data='3'),
                     InlineKeyboardButton("Friday", callback_data='4'),
                     InlineKeyboardButton("Saturday", callback_data='5')],
                    [InlineKeyboardButton("Confirm", callback_data='-2')]]

        selected_days = ", ".join([days[i] for i in chat_data['tmpjob']['days']])
        bot.edit_message_text(text="Select another day or confirm:\n{}".format(selected_days),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=InlineKeyboardMarkup(keyboard))


def unset(bot, update, args, chat_data):
    if str(update.message.chat_id) in allowed_id:
        try:
            name_job = args[0]
            if name_job in chat_data and name_job in threads:
                job = chat_data[name_job]["job"]
                job.schedule_removal()

                del threads[name_job]
                del chat_data[name_job]

                update.message.reply_text('Job <b>{}</b> successfully unset!'.format(name_job), parse_mode='HTML')
            else:
                update.message.reply_text("Sorry, job named <b>{}</b> was not found.".format(name_job),
                                          parse_mode='HTML')
        except (IndexError, ValueError):
            update.message.reply_text('Usage: /unset <name_job>')
    else:
        message = 'You have not the permission to use this bot.\nFor more details visit [Telegram-InstaPy-Scheduling](https://github.com/Tkd-Alex/Telegram-InstaPy-Scheduling)'
        update.message.reply_text(message, parse_mode='Markdown')


def list_jobs(bot, update, chat_data):
    message = ""
    if len(chat_data) > 0:
        for job in chat_data:
            message = message + "- <b>Job name:</b> {} <b>Script name:</b> {} <b>Username:</b> {} <b>Schedule at</b>: {} <b>Days:</b> {}\n".format(
                chat_data[job]["name"], chat_data[job]["script_name"], chat_data[job]["username"],
                chat_data[job]["scheduled"], chat_data[job]["days"])
        update.message.reply_text(message, parse_mode='HTML')
    else:
        update.message.reply_text("You are 0 jobs setted")


def list_scripts(bot, update):
    message = "You have <b>{}</b> scripts configured.".format(len(scripts))
    index = 1
    for script in scripts:
        message += "\n{}) <b>{}</b>".format(index, script)
        index += 1
    update.message.reply_text(message, parse_mode='HTML')


if __name__ == '__main__':
    updater = Updater(telegram_token)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", help))
    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(CommandHandler("status", status_thread, pass_args=True))

    dp.add_handler(CommandHandler("set", set, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("now", now, pass_args=True))

    dp.add_handler(CommandHandler("unset", unset, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("jobs", list_jobs, pass_chat_data=True))

    dp.add_handler(CommandHandler("scripts", list_scripts))

    dp.add_handler(CallbackQueryHandler(day_choose, pass_job_queue=True, pass_chat_data=True))

    updater.start_polling()

    updater.idle()
