#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
from thread import Thread

content_file = "settings/content.json"


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
        with open(content_file, "r") as f:
            content = json.load(f)
    except:
        return {"commenti": {}, "hashtag": {}, "follow": [], "amount": 0}

    try:
        content["amount"] = int(content["amount"])
    except:
        content["amount"] = 1
    return content


def save_content(content):
    with open(content_file, "w") as f:
        json.dump(content, f)
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
        attribute['username'],
        attribute['password'],
        attribute['cartella_commenti']
    )
    return new_thread
