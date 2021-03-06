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
    def __init__(self, job_name, script_name, chat_id, bot, username, password, cartella_commenti):
        threading.Thread.__init__(self)
        self.job_name = job_name
        self.script_name = script_name
        self.chat_id = chat_id
        self.bot = bot
        self.username = username
        self.password = password
        self.cartella_commenti = cartella_commenti

    def return_attribute(self):
        return {
            "job_name": self.job_name,
            "script_name": self.script_name,
            "chat_id": self.chat_id,
            "bot": self.bot,
            "username": self.username,
            "password": self.password,
            "cartella_commenti": self.cartella_commenti
        }

    def run(self):
        start = datetime.datetime.now().replace(microsecond=0)
        self.bot.send_message(self.chat_id,
                              text="*{}*\n\nStart 🕓 {}".format(self.job_name, time.strftime("%X")),
                              parse_mode="Markdown"
                              )

        # run the script
        try:
            importlib.reload(scripts)
            scripts._get_scripts()[self.script_name](self.username, self.password, self.cartella_commenti)
        except ValueError:
            traceback.print_exc()
            print("Error! Signal not in main thread!")

        end = datetime.datetime.now().replace(microsecond=0)
        self.bot.send_message(self.chat_id,
                              text='*{}*\n\nEnd 🕓 {}\nDurata ⌚ {}'.
                              format(self.job_name, time.strftime("%X"), end - start),
                              parse_mode="Markdown"
                              )

        # Read the last 9 line to get ended status of InstaPy.
        try:
            logfile = open('instapy/logs/' + self.username + '/general.log', "r").readlines()
            lines = logfile[-7:]
            message = re.sub("INFO \[.*\] \[.*\]", "", "".join(lines))
        except:
            message = "Unable to read InstaPy log!"

        self.bot.send_message(self.chat_id, text=message)
