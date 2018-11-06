#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from instapy.instapy import InstaPy
from instapy.instapy.util import smart_run
import utils


# Create your script here:

def likehashtag(username, password):
    content = utils.load_content()
    session = InstaPy(username=username,
                      password=password,
                      headless_browser=True,
                      disable_image_load=False)
    with smart_run(session):
        session.set_relationship_bounds(enabled=False, delimit_by_numbers=False)
        session.like_by_tags(content["hashtag"], amount=content["amount"])


def buongiornissimo(username, password):
    session = InstaPy(username=username,
                      password=password,
                      headless_browser=True,
                      disable_image_load=True)
    with smart_run(session):
        session.set_relationship_bounds(enabled=False, delimit_by_numbers=False)
        session.set_do_comment(enabled=True, percentage=100)
        session.set_comments(['Buongiorno! 😊 Bellissima foto e complimenti per la tua galleria, fantastica! 🔝 Ti va \
        di passare dal mio profilo e seguirmi se ti piacciono i miei lavori? 📸'])
        session.like_by_tags(["buongiorno"], amount=_get_amount(), media="Photo")


def commenthashtag(username, password):
    session = InstaPy(username=username,
                      password=password,
                      headless_browser=True,
                      disable_image_load=True)
    with smart_run(session):
        session.set_relationship_bounds(enabled=False, delimit_by_numbers=False)
        session.set_do_comment(enabled=True, percentage=100)
        session.set_comments(_get_comments())
        session.like_by_tags(_get_hashtags(), amount=_get_amount(), media="Photo")


def followfollowers(username, password):
    session = InstaPy(username=username,
                      password=password,
                      headless_browser=True,
                      disable_image_load=True)
    with smart_run(session):
        session.set_relationship_bounds(enabled=False, delimit_by_numbers=False)
        session.follow_user_followers(_get_follow(), amount=_get_amount(), randomize=False)


def unfollow(username, password):
    session = InstaPy(username=username,
                      password=password,
                      headless_browser=True,
                      disable_image_load=True)
    with smart_run(session):
        session.unfollow_users(amount=99999, InstapyFollowed=(True, "all"), style="FIFO", unfollow_after=1,
                               sleep_delay=2)


# !! Not delete the following code.


def _get_amount():
    try:
        a = open("settings/amount.txt", encoding="utf-8").readlines()
        return int(a[0])
    except:
        print("Unable to read amount!")
        raise


def _get_hashtags():
    try:
        a = open("settings/tags.txt", encoding="utf-8").readlines()
        return a
    except:
        print("Unable to read hashtags!")
        raise


def _get_comments():
    try:
        a = open("settings/comments.txt", encoding="utf-8").readlines()
        return a
    except:
        print("Unable to read comments!")
        raise


def _get_follow():
    try:
        a = open("settings/follow.txt", encoding="utf-8").readlines()
        return a
    except:
        print("Unable to read user to follow!")
        raise


def _get_scripts():
    scripts_list = {}
    functions = [f for fname, f in sorted(globals().items()) if callable(f)]
    for f in functions:
        if str(f.__name__)[0] == "_":
            # avoiding functions that starts with "_"
            continue
        elif str(f.__name__).lower() in ["smart_run", "instapy"]:
            continue
        scripts_list[str(f.__name__).lower()] = f
    return scripts_list


_get_scripts()  # loading scripts first time
