#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import module
import importlib
import os
import json
import pickle
import time
import logging
import subprocess
from threading import Event
from time import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

import scripts
from utils import *

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load settings
with open('settings.json') as f:
    settings = json.load(f)

telegram_token = settings['telegram_token']
allowed_id = settings['allowed_id']
user = {'username': settings['insta_user'], 'password': settings['insta_pass'], 'proxy': None}

# Setup base folder
os.chdir(settings['base_folder'])
print(os.getcwd())

# Create array with all threads
threads = {}

# Error message
error_message = "This bot no longer works."

# Command status
reading_hashtags = False
reading_comments = False

# Lists
hashtag_list = []
comments_list = []

jobs_file = "settings/jobs.pkl"
hashtag_file = "settings/tags.txt"
amount_file = "settings/amount.txt"
comments_file = "settings/comments.txt"


def now(bot, update, args):
    if not chatid_is_valid(update, allowed_id, error_message):
        return
    try:

        if not args[0] in scripts._get_scripts():
            update.message.reply_text("Sorry, script named <b>{}</b> is not in your scripts file.".format(args[0]),
                                      parse_mode='HTML')
            return

        job_name = "{}_temp_{}".format(args[0], time())
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


def set_hashtag(bot, update):
    global reading_hashtags
    global reading_comments
    global hashtag_list
    update.message.reply_text("Inviami gli hashtag uno alla volta (senza #)")
    update.message.reply_text("Per terminare manda #")
    hashtag_list = []
    reading_hashtags = True
    reading_comments = False


def set_comments(bot, update):
    global reading_comments
    global reading_hashtags
    global comments_list
    update.message.reply_text("Inviami i commenti uno alla volta")
    update.message.reply_text("Per terminare manda #")
    comments_list = []
    reading_hashtags = False
    reading_comments = True


def set_amount(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("Uso: /set_amount xyz")
        try:
            with open(amount_file, "r", encoding="utf-8") as f:
                amnt = f.readlines()[0]
            update.message.reply_text("Valore attuale: *" + amnt + "*", parse_mode="Markdown")
            return
        except:
            return

    try:
        with open(amount_file, "w", encoding="utf-8") as f:
            f.write(args[0])
    except:
        update.message.reply_text("Impossibile impostare il valore!")
        return

    update.message.reply_text("Impostato il valore a " + args[0])


def show_hashtag(bot, update):
    if not chatid_is_valid(update, allowed_id, error_message):
        return

    update.message.reply_text("*Hashtag salvati*", parse_mode="Markdown")
    try:
        lista = open(hashtag_file, "r", encoding="utf-8").readlines()
        messaggio = ""
        for line in lista:
            messaggio += line + "\n"
        update.message.reply_text(messaggio)
    except:
        update.message.reply_text("Nessun hashtag salvato!")


def show_comments(bot, update):
    if not chatid_is_valid(update, allowed_id, error_message):
        return

    update.message.reply_text("*Commenti salvati*", parse_mode="Markdown")
    try:
        lista = open(comments_file, "r", encoding="utf-8").readlines()
        messaggio = ""
        for line in lista:
            messaggio += line + "\n"
        update.message.reply_text(messaggio)
    except:
        update.message.reply_text("Nessun commento salvato!")


def message_handler(bot, update):
    if not chatid_is_valid(update, allowed_id, error_message):
        return

    global reading_hashtags
    global hashtag_list
    global reading_comments
    global comments_list

    if reading_hashtags:
        text = update.message.text
        print(text)
        update.message.reply_text(text)
        if "#" not in text:
            hashtag_list.append(text)
        else:
            with open(hashtag_file, "w", encoding="utf-8") as f:
                f.writelines("%s\n" % tag for tag in hashtag_list)
            update.message.reply_text("Ok, ho salvato gli hashtag!")
            reading_hashtags = False
    elif reading_comments:
        text = update.message.text
        print(text)
        update.message.reply_text(text)
        if "#" not in text:
            comments_list.append(text)
        else:
            with open(comments_file, "w", encoding="utf-8") as f:
                f.writelines("%s\n" % comment for comment in comments_list)
            update.message.reply_text("Ok, ho salvato i commenti!")
            reading_comments = False


def stop(bot, update):
    if not chatid_is_valid(update, allowed_id, error_message):
        return

    update.message.reply_text("Restarting the bot. Please wait...")
    subprocess.Popen(["restart.sh"], stdin=subprocess.PIPE)

def status_thread(bot, update, args):
    if not chatid_is_valid(update, allowed_id, error_message):
        return
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


def set(bot, update, args, chat_data):
    if not chatid_is_valid(update, allowed_id, error_message):
        return

    try:
        if args[0] in chat_data or args[1] in threads:
            update.message.reply_text("Sorry, job named <b>{}</b> is already used.".format(args[0]),
                                      parse_mode='HTML')
            return

        if not args[1] in scripts._get_scripts():
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
        update.message.reply_text('Usage: /set <job_name> <script_name> <hh:mm>')


def day_choose(bot, update, chat_data):
    global job_queue
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

    save_jobs()


def unset(bot, update, args, chat_data):
    if not chatid_is_valid(update, allowed_id, error_message):
        return

    try:
        job_queue.get_jobs_by_name(args[0])[0].schedule_removal()
        update.message.reply_text('Job <b>{}</b> successfully unset!'.format(args[0]), parse_mode='HTML')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /unset <job_name>')

    save_jobs()


def list_jobs(bot, update, chat_data):
    if not chatid_is_valid(update, allowed_id, error_message):
        return

    jobs = job_queue.jobs()
    for j in jobs:
        if not j.removed:
            update.message.reply_text(j.name)


def list_scripts(bot, update):
    if not chatid_is_valid(update, allowed_id, error_message):
        return
    scripts_list = scripts._get_scripts()
    message = "You have <b>{}</b> scripts configured.".format(len(scripts_list))
    index = 1
    for script in scripts_list:
        message += "\n{}) <b>{}</b>".format(index, script)
        index += 1
    update.message.reply_text(message, parse_mode='HTML')


def reload_scripts(bot, update):
    if not chatid_is_valid(update, allowed_id, error_message):
        return
    importlib.reload(scripts)
    update.message.reply_text("Scripts reloaded!")


def load_jobs():
    global job_queue
    now = time()

    with open(jobs_file, 'rb') as fp:
        while True:
            try:
                next_t, job = pickle.load(fp)
            except EOFError:
                break  # Loaded all job tuples

            # Create threading primitives
            enabled = job._enabled
            removed = job._remove

            job._enabled = Event()
            job._remove = Event()

            if enabled:
                job._enabled.set()

            if removed:
                job._remove.set()

            next_t -= now  # Convert from absolute to relative time

            job_queue._put(job, next_t)


def save_jobs():
    global job_queue

    if job_queue:
        job_tuples = job_queue._queue.queue
    else:
        job_tuples = []

    with open(jobs_file, 'wb') as fp:
        for next_t, job in job_tuples:
            # Back up objects
            _job_queue = job._job_queue
            _remove = job._remove
            _enabled = job._enabled

            # Replace un-pickleable threading primitives
            job._job_queue = None  # Will be reset in jq.put
            job._remove = job.removed  # Convert to boolean
            job._enabled = job.enabled  # Convert to boolean

            # Pickle the job
            pickle.dump((next_t, job), fp)

            # Restore objects
            job._job_queue = _job_queue
            job._remove = _remove
            job._enabled = _enabled


if __name__ == '__main__':

    updater = Updater(telegram_token)
    dp = updater.dispatcher

    job_queue = updater.job_queue

    try:
        load_jobs()
    except FileNotFoundError:
        pass

    dp.add_handler(CommandHandler("status", status_thread, pass_args=True))
    dp.add_handler(CommandHandler("set", set, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("now", now, pass_args=True))
    dp.add_handler(CommandHandler("unset", unset, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("jobs", list_jobs, pass_chat_data=True))
    dp.add_handler(CommandHandler("scripts", list_scripts))
    dp.add_handler(CommandHandler("set_hashtag", set_hashtag))
    dp.add_handler(CommandHandler("hashtag", show_hashtag))
    dp.add_handler(CommandHandler("set_amount", set_amount, pass_args=True))
    dp.add_handler(CommandHandler("set_comments", set_comments))
    dp.add_handler(CommandHandler("comments", show_comments))
    dp.add_handler(CommandHandler("stop", stop))

    dp.add_handler(CommandHandler("reload_scripts", reload_scripts))

    dp.add_handler(MessageHandler(Filters.text, message_handler))

    dp.add_handler(CallbackQueryHandler(day_choose, pass_chat_data=True))

    updater.start_polling()

    updater.idle()

    # save_jobs(job_queue)
