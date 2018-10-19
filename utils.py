#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from thread import Thread


def chatid_is_valid(update, allowed_id, error_message):
    if str(update.message.chat_id) not in allowed_id:
        update.message.reply_text(error_message)
        return False
    else:
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


