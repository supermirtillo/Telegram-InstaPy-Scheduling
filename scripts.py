#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback
from instapy.instapy import InstaPy
from instapy.instapy.util import smart_run


# Create your script here:
def awesome(username, password, proxy):
    try:
        session = instapy.InstaPy(username=username, password=password)
        session.login()
        session.end()
    except:
        print(traceback.format_exc())


def likehashtag(username, password, proxy):
    session = InstaPy(username=username,
                      password=password,
                      headless_browser=True,
                      disable_image_load=False)
    with smart_run(session):
        try:
            tags = open("settings/tags.txt", encoding="utf-8").readlines()
        except:
            print("=== Errore nel leggere gli hashtag. Finisco qui! ===")

        session.set_relationship_bounds(enabled=False, delimit_by_numbers=False)
        session.like_by_tags(tags, amount=200)

def commenthashtag(username, password, proxy):
    session = InstaPy(username=username,
                      password=password,
                      headless_browser=True,
                      disable_image_load=False)
    with smart_run(session):
        try:
            tags = open("settings/tags.txt", encoding="utf-8").readlines()
            comments = open("settings/comments.txt", encoding="utf-8").readlines()
        except:
            print("               === Unable to read ./settings/*.txt files ===")
            return

        session.set_relationship_bounds(enabled=False, delimit_by_numbers=False)
        session.set_do_comment(enabled=True, percentage=100)
        session.set_comments(comments)
        session.like_by_tags(tags, amount=200)


def biglikers(username, password, proxy):
    try:
        session = instapy.InstaPy(username=username, password=password)
        session.login()
        session.end()
    except:
        print(traceback.format_exc())


# !! Not delete the following code.

functions = [f for fname, f in sorted(globals().items()) if callable(f)]
scripts = {}
for function in functions:
    scripts[str(function.__name__).lower()] = function
