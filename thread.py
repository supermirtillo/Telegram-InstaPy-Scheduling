#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import threading
import time
import importlib
import re
import traceback

import scripts


class Thread(threading.Thread):
    def __init__(self, job_name, script_name, chat_id, bot, username, password, proxy=None):
        threading.Thread.__init__(self)
        self.job_name = job_name
        self.script_name = script_name
        self.chat_id = chat_id
        self.bot = bot
        self.username = username
        self.password = password
        self.proxy = proxy

    def return_attribute(self):
        return {
            "job_name": self.job_name,
            "script_name": self.script_name,
            "chat_id": self.chat_id,
            "bot": self.bot,
            "user": {
                "username": self.username,
                "password": self.password,
                "proxy": self.proxy
            }
        }

    def run(self):
        start = datetime.datetime.now().replace(microsecond=0)
        self.bot.send_message(self.chat_id,
                              text='InstaPy Bot - {} start at {}'.format(self.job_name, time.strftime("%X")))

        # run the script
        try:
            importlib.reload(scripts)
            scripts._get_scripts()[self.script_name](self.username, self.password)
        except ValueError:
            traceback.print_exc()
            print("Error! Signal not in main thread!")

        end = datetime.datetime.now().replace(microsecond=0)
        self.bot.send_message(self.chat_id,
                              text='InstaPy Bot end at {}\nExecution time {}'.format(time.strftime("%X"), end - start))

        # Read the last 9 line to get ended status of InstaPy.
        try:
            logfile = open('instapy/logs/' + self.username + '/general.log', "r").readlines()
            lines = logfile[-7:]
            message = re.sub("INFO \[.*\] \[.*\]", "", lines)
        except:
            message = "Unable to read InstaPy log!"

        self.bot.send_message(self.chat_id, text=message)
