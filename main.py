#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import module
import importlib
import json
import logging
import os
import pickle
import subprocess
from functools import wraps
from threading import Event
from time import time, strftime

import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# librerie utente
import scripts
import utils

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load settings
with open('settings.json') as f:
    settings = json.load(f)

telegram_token = settings['telegram_token']
allowed_id = settings['allowed_id']
user = {'username': settings['insta_user'], 'password': settings['insta_pass'], 'proxy': None}
content = utils.load_content()

# dizionario per salvare il valore corrente della cartella corrente per gli hashtag
# e per i commenti
cartella_corrente = {"commenti": None, "hashtag": None}

print(os.getcwd())

# Crea array con tutti i thread
threads = {}

# Messaggio di errore per quando l'utente non è autenticato
error_message = "This bot no longer works."

# Lists
hashtag_list = []
comments_list = []

jobs_file = "settings/jobs.pkl"
follow_file = "settings/follow.txt"


def restricted(func):
    """
    Definisco il decorator @restricted per controllare l'accesso ai comandi
    """

    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if str(user_id) not in allowed_id:
            update.message.reply_text(error_message)
            return
        return func(bot, update, *args, **kwargs)

    return wrapped


def now_conv(bot, update):
    tastiera = telegram.ReplyKeyboardMarkup(
        utils.create_button_layout(
            list(content["commenti"].keys()),
            3),
        resize_keyboard=True
    )
    update.message.reply_text("👉 Scegli la cartella dei *commenti*", parse_mode="Markdown", reply_markup=tastiera)

    return CARTELLA_COMMENTI_NOW


@restricted
def cartella_commenti_now(bot, update):
    global cartella_corrente
    text = update.message.text
    cartella_corrente["commenti"] = text

    # passo alla lista delle cartelle degli hashtag
    tastiera = telegram.ReplyKeyboardMarkup(utils.create_button_layout(list(content["hashtag"].keys()), 3),
                                            resize_keyboard=True
                                            )
    update.message.reply_text("👉 Scegli la cartella degi *hashtag*", parse_mode="Markdown", reply_markup=tastiera)
    return CARTELLA_HASHTAG_NOW


@restricted
def cartella_hashtag_now(bot, update):
    global cartella_corrente

    text = update.message.text
    cartella_corrente["hashtag"] = text

    scripts_list = list(scripts._get_scripts().keys())
    tastiera_script = telegram.ReplyKeyboardMarkup(utils.create_button_layout(scripts_list, 2), resize_keyboard=True)

    risposta = "*Cartella commenti*:\n  📝 {}\n\n".format(cartella_corrente["commenti"])
    risposta += "*Cartella hashtag*:\n  🏷️ {}\n\n".format(cartella_corrente["hashtag"])

    n_hashtag = len(content["hashtag"][cartella_corrente["hashtag"]])
    risposta += "*Interazioni totali*:\n  🤝 {}".format(content["amount"] * n_hashtag)
    update.message.reply_text(risposta, parse_mode="Markdown")

    update.message.reply_text("👉 Scegli uno *script*:", parse_mode="Markdown",
                              reply_markup=tastiera_script)
    return SCRIPT_NOW


@restricted
def script_now(bot, update):
    script = update.message.text
    update.message.reply_text("Sto facendo partire lo script *{}*...".format(script), parse_mode="Markdown",
                              reply_markup=telegram.ReplyKeyboardRemove())

    job_name = "{} - {}".format(script, strftime("%m%d_%H%M"))
    temp_thread = utils.Thread(
        job_name,
        script,
        update.message.chat_id,
        bot,
        user['username'],
        user['password'],
        cartella_corrente
    )
    temp_thread.start()
    return ConversationHandler.END


def exec_thread(bot, job):
    if threads[job.name].isAlive():
        bot.send_message(threads[job.name].chat_id, text="Sorry <b>{}</b> already executing!".format(job.name),
                         parse_mode='HTML')
    else:
        threads[job.name] = utils.reload_thread(threads[job.name])
        threads[job.name].start()


def create_thread(bot, context):
    threads[context['job_name']] = utils.Thread(
        context['job_name'],
        context['script_name'],
        context['chat_id'],
        bot,
        context['user']['username'],
        context['user']['password'],
        context['user']['proxy']
    )


@restricted
def lista_cartelle_hashtag(bot, update):
    return lista_cartelle_generale(bot, update, "hashtag", CARTELLA_HASHTAG)


@restricted
def leggi_cartella_hashtag(bot, update):
    return leggi_cartella_generale(bot, update, "hashtag", MODIFICA_HASHTAG)


@restricted
def modifica_hashtag(bot, update):
    return modifica_cartella_generale(bot, update, "hashtag", LEGGI_HASHTAG)


@restricted
def leggi_hashtag(bot, update):
    return leggi_generale(bot, update, "hashtag")


@restricted
def lista_cartelle_commenti(bot, update):
    return lista_cartelle_generale(bot, update, "commenti", CARTELLA_COMMENTI)


@restricted
def leggi_cartella_commenti(bot, update):
    return leggi_cartella_generale(bot, update, "commenti", MODIFICA_COMMENTI)


@restricted
def modifica_commenti(bot, update):
    return modifica_cartella_generale(bot, update, "commenti", LEGGI_COMMENTI)


@restricted
def leggi_commenti(bot, update):
    return leggi_generale(bot, update, "commenti")


@restricted
def lista_cartelle_generale(bot, update, tipo: str, return_value_folder):
    """
    Mostro all'utente la lista delle cartelle salvate
    """
    tastiera = telegram.ReplyKeyboardMarkup(
        utils.create_button_layout(
            list(content[tipo].keys()),
            3),
        resize_keyboard=True
    )
    risposta = "👉 *Scegli* la cartella\n\n      _oppure_\n\n👉 *Scrivi* il nome di una cartella per crearla"
    update.message.reply_text(risposta, parse_mode="Markdown", reply_markup=tastiera)

    return return_value_folder  # passo allo stato di lettura della cartellao


@restricted
def leggi_cartella_generale(bot, update, tipo: str, return_value_edit):
    """
    Richiesta all'utente della cartella generale
    :param tipo: il nome del tipo di cartella "hashtag" oppure "commenti"
    :param return_value_edit: il valore di ritorno (il nuovo stato della conversazione)
    :return: lo stato del ritorno definito da return_value
    """

    global cartella_corrente
    global content

    # errore nel passaggio dei parametri, finisco la conversazione
    if (tipo != "commenti") and (tipo != "hashtag"):
        return fine_conversazione(bot, update)

    # imposto la cartella corrente come il messaggio che ho appena letto
    cartella_corrente[tipo] = update.message.text

    # se la cartella esiste (non devo crearla) procedo ad elencare tutti i valori che contiene
    if cartella_corrente[tipo] in list(content[tipo].keys()):
        risposta = "*Cartella di {}*:\n  🔥 {}".format(tipo, cartella_corrente[tipo])

        risposta += "\n\n*{} salvati*:".format(tipo.capitalize())
        for item in content[tipo][cartella_corrente[tipo]]:
            risposta += "\n▫️ {}".format(item)

        # mando il messaggio e chiedo all'utente che cosa vuole fare di questa cartella
        update.message.reply_text(risposta, parse_mode="Markdown",
                                  reply_markup=telegram.ReplyKeyboardMarkup(
                                      [["🔄  Riscrivi", "✏️ Aggiungi"],
                                       ["❌  Elimina", "✅ Fine"]],
                                      resize_keyboard=True
                                  ))
        return return_value_edit

    # se la cartella nel messaggio non esiste la creo e poi passo alla return_value
    else:
        content[tipo][cartella_corrente[tipo]] = []
        utils.save_content(content)
        update.message.reply_text("Nuova cartella *{}* creata. La troverai in /{}".
                                  format(cartella_corrente[tipo], tipo),
                                  parse_mode="Markdown")
        return fine_conversazione(bot, update)


@restricted
def modifica_cartella_generale(bot, update, tipo: str, return_value_read):
    global content
    comando = update.message.text.lower()

    if (tipo != "commenti") and (tipo != "hashtag"):
        # se ho un errore nel passaggio dei parametri finisco la conversazione
        return fine_conversazione(bot, update)

    elif "riscrivi" in comando:
        update.message.reply_text("🔄  Riscrivi *{}* (cartella di *{}*)\nManda *#* per terminare".
                                  format(cartella_corrente[tipo], tipo),
                                  parse_mode="Markdown", reply_markup=telegram.ReplyKeyboardRemove())
        # resetto il contetnuto della cartella prima di leggere (leggere eseguirà .append())
        content[tipo][cartella_corrente[tipo]] = []
        return return_value_read

    elif "aggiungi" in comando:
        update.message.reply_text("✏️ Aggiungi a *{}* (cartella di *{}*)\nManda *#* per terminare".
                                  format(cartella_corrente[tipo], tipo),
                                  parse_mode="Markdown", reply_markup=telegram.ReplyKeyboardRemove())
        return return_value_read

    elif "elimina" in comando:
        update.message.reply_text("❌  Cartella di {} *{}* eliminata!".format(tipo, cartella_corrente[tipo]),
                                  parse_mode="Markdown", reply_markup=telegram.ReplyKeyboardRemove())
        del content[tipo][cartella_corrente[tipo]]
        utils.save_content(content)
        return ConversationHandler.END
    else:
        return fine_conversazione(bot, update)


@restricted
def leggi_generale(bot, update, tipo: str):
    global content

    text = update.message.text

    # se ho degli hashtag li voglio tutti minuscoli
    if tipo == "hashtag":
        text = text.lower()

    if text == "#":
        update.message.reply_text("*{} salvati* 😎".format(tipo.capitalize()), parse_mode="Markdown")
        return ConversationHandler.END

    content[tipo][cartella_corrente[tipo]].append(text)
    utils.save_content(content)


@restricted
def cancel(bot, update):
    update.message.reply_text("⛔️ *Comando annullato*", parse_mode="Markdown",
                              reply_markup=telegram.ReplyKeyboardRemove())
    return ConversationHandler.END


def fine_conversazione(bot, update):
    update.message.reply_text("*Fine*", parse_mode="Markdown",
                              reply_markup=telegram.ReplyKeyboardRemove())
    return ConversationHandler.END


@restricted
def follow(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("Uso: /set\_follow *username*", parse_mode="Markdown")
        try:
            with open(follow_file, "r", encoding="utf-8") as f:
                user = f.readlines()[0]
            update.message.reply_text("Utente attuale: *" + user + "*", parse_mode="Markdown")
            return
        except:
            return

    try:
        with open(follow_file, "w", encoding="utf-8") as f:
            f.write(args[0])
    except:
        update.message.reply_text("Impossibile salvare l'utente!")
        return

    update.message.reply_text("Salvato utente *" + args[0] + "*", parse_mode="Markdown")


@restricted
def set_amount(bot, update):
    update.message.reply_text("Valore attuale: *{}*".format(content["amount"]), parse_mode="Markdown",
                              reply_markup=telegram.ReplyKeyboardMarkup([["✏️ Modifica", "✅ Fine"]],
                                                                        resize_keyboard=True)
                              )
    return MODIFICA_AMOUNT


@restricted
def modifica_amount(bot, update):
    text = update.message.text
    if "modifica" in text.lower():
        update.message.reply_text("Scrivi il nuovo valore:", reply_markup=telegram.ReplyKeyboardRemove())
        return LEGGI_AMOUNT
    else:
        return fine_conversazione(bot, update)


@restricted
def leggi_amount(bot, update):
    text = update.message.text
    try:
        amt = int(text)
    except ValueError:
        update.message.reply_text("Attenzione! Valore non valido. Inserire un numero!")
        return LEGGI_AMOUNT

    content["amount"] = amt
    utils.save_content(content)

    update.message.reply_text("*Valore salvato* 👍", parse_mode="Markdown")
    return ConversationHandler.END


@restricted
def stop(bot, update):
    update.message.reply_text("Bot restarted!")
    subprocess.Popen([os.path.abspath("restart.sh")], stdin=subprocess.PIPE)


@restricted
def status_thread(bot, update, args):
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


@restricted
def set(bot, update, args, chat_data):
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

        keyboard = [[telegram.InlineKeyboardButton("Sunday", callback_data='6'),
                     telegram.InlineKeyboardButton("Monday", callback_data='0'),
                     telegram.InlineKeyboardButton("Tuesday", callback_data='1'),
                     telegram.InlineKeyboardButton("Wednesday", callback_data='2')],
                    [telegram.InlineKeyboardButton("Thursday", callback_data='3'),
                     telegram.InlineKeyboardButton("Friday", callback_data='4'),
                     telegram.InlineKeyboardButton("Saturday", callback_data='5')],
                    [telegram.InlineKeyboardButton("Everyday", callback_data='-1')]]

        update.message.reply_text('Choose a day: ', reply_markup=telegram.InlineKeyboardMarkup(keyboard))
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <job_name> <script_name> <hh:mm>')


def day_choose(bot, update, chat_data):
    global job_queue
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    query = update.callback_query

    scheduled_time = utils.parse_time(chat_data['tmpjob']['scheduled'])
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

        keyboard = [[telegram.InlineKeyboardButton("Sunday", callback_data='6'),
                     telegram.InlineKeyboardButton("Monday", callback_data='0'),
                     telegram.InlineKeyboardButton("Tuesday", callback_data='1'),
                     telegram.InlineKeyboardButton("Wednesday", callback_data='2')],
                    [telegram.InlineKeyboardButton("Thursday", callback_data='3'),
                     telegram.InlineKeyboardButton("Friday", callback_data='4'),
                     telegram.InlineKeyboardButton("Saturday", callback_data='5')],
                    [telegram.InlineKeyboardButton("Confirm", callback_data='-2')]]

        selected_days = ", ".join([days[i] for i in chat_data['tmpjob']['days']])
        bot.edit_message_text(text="Select another day or confirm:\n{}".format(selected_days),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=telegram.InlineKeyboardMarkup(keyboard))

    save_jobs()


@restricted
def unset(bot, update, args, chat_data):
    try:
        job_queue.get_jobs_by_name(args[0])[0].schedule_removal()
        update.message.reply_text('Job <b>{}</b> successfully unset!'.format(args[0]), parse_mode='HTML')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /unset <job_name>')

    save_jobs()


@restricted
def list_jobs(bot, update, chat_data):
    jobs = job_queue.jobs()
    for j in jobs:
        if not j.removed:
            update.message.reply_text(j.name)


@restricted
def list_scripts(bot, update):
    scripts_list = scripts._get_scripts()
    message = "You have <b>{}</b> scripts configured.".format(len(scripts_list))
    index = 1
    for script in scripts_list:
        message += "\n{}) <b>{}</b>".format(index, script)
        index += 1
    update.message.reply_text(message, parse_mode='HTML')


@restricted
def reload_scripts(bot, update):
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

    dp.add_handler(CallbackQueryHandler(day_choose, pass_chat_data=True))
    dp.add_handler(CommandHandler("status", status_thread, pass_args=True))
    dp.add_handler(CommandHandler("set", set, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("jobs", list_jobs, pass_chat_data=True))
    dp.add_handler(CommandHandler("scripts", list_scripts))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("set_follow", follow, pass_args=True))
    dp.add_handler(CommandHandler("reload_scripts", reload_scripts))

    # conversazione per l'aggiunta e la visione dei commenti salvati
    CARTELLA_COMMENTI, LEGGI_COMMENTI, MODIFICA_COMMENTI = range(3)

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("commenti", lista_cartelle_commenti)],
        states={
            CARTELLA_COMMENTI: [MessageHandler(Filters.text, leggi_cartella_commenti)],
            MODIFICA_COMMENTI: [MessageHandler(Filters.text, modifica_commenti)],
            LEGGI_COMMENTI: [MessageHandler(Filters.text, leggi_commenti)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True
    ))

    # conversazione per l'aggiunta e la visualizzazione degli hashtag
    CARTELLA_HASHTAG, MODIFICA_HASHTAG, LEGGI_HASHTAG = range(3)

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("hashtag", lista_cartelle_hashtag)],
        states={
            CARTELLA_HASHTAG: [MessageHandler(Filters.text, leggi_cartella_hashtag)],
            MODIFICA_HASHTAG: [MessageHandler(Filters.text, modifica_hashtag)],
            LEGGI_HASHTAG: [MessageHandler(Filters.text, leggi_hashtag)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True
    ))

    # conversazione per l'impostazione dell'amount
    MODIFICA_AMOUNT, LEGGI_AMOUNT = range(2)

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("amount", set_amount)],
        states={
            LEGGI_AMOUNT: [MessageHandler(Filters.text, leggi_amount)],
            MODIFICA_AMOUNT: [MessageHandler(Filters.text, modifica_amount)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True
    ))

    # conversazione per now
    CARTELLA_COMMENTI_NOW, CARTELLA_HASHTAG_NOW, SCRIPT_NOW = range(3)

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("esegui", now_conv)],
        states={
            CARTELLA_COMMENTI_NOW: [MessageHandler(Filters.text, cartella_commenti_now)],
            CARTELLA_HASHTAG_NOW: [MessageHandler(Filters.text, cartella_hashtag_now)],
            SCRIPT_NOW: [MessageHandler(Filters.text, script_now)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True
    ))

    updater.start_polling()

    updater.idle()

    # save_jobs(job_queue)
