#! /bin/bash

pkill -9 python3
pkill -9 chrome

sleep 2

cd /home/luca/instapy/Telegram-InstaPy-Scheduling
nohup python3 ./main.py
