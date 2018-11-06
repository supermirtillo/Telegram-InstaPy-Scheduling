#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import pickle
from thread import Thread

pickle_file = "settings/content.pkl"


def chatid_is_valid(update, allowed_id, error_message):
    if str(update.message.chat_id) not in allowed_id:
        update.message.reply_text(error_message)
        return False
    else:
        return True


def create_button_layout(lista, col_n):
    """
    Crea il layout per la tastiera di risposta da una lista lineare
    :param lista: Lista lineare da cui creare l'array di bottoni
    :param col_n: Numero di colonne
    :return: Layout per Telegram
    """
    return [lista[i:i + col_n] for i in range(0, len(lista), col_n)]


def load_content():
    try:
        with open(pickle_file, "rb") as f:
            content = pickle.load(f)
    except:
        return {"comments": {}, "hashtags": [], "follow": [], "amount": 0}

    try:
        content["amount"] = int(content["amount"])
    except:
        pass
    return content


def save_content(content):
    with open(pickle_file, "wb") as f:
        pickle.dump(content, f)
        return True


def parse_time(time):
    time = time.split(":")
    h = int(time[0])
    m = int(time[1])
    time = datetime.time(h, m, 0)
    return time


def reload_thread(thread):
    attribute = thread.return_attribute()
    new_thread = Thread(
        attribute['job_name'],
        attribute['script_name'],
        attribute['chat_id'],
        attribute['bot'],
        attribute['user']['username'],
        attribute['user']['password'],
        attribute['user']['proxy']
    )
    return new_thread
