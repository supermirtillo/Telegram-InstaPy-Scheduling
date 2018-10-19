# Telegram-InstaPy-Scheduling v2!
Telegram-InstaPy-Scheduling is bot for telegram which helps user to schedule [*InstaPy*](https://github.com/timgrossmann/InstaPy).

### What's news?
- Run multiple script simultaneous.
- Configure your scripts in easy way!
- Create users list.

### Setup
- Install _requirements.txt_ (`$ pip install -r requirements.txt`)
- Clone InstaPy in `./instapy/`
- Create a bot with [@BotFather](https://telegram.me/BotFather)
- Rename *settings.json.dist* ➡ *settings.json*
- Contact [@GiveChatId_Bot](https://telegram.me/GiveChatId_Bot) and get your chat id with `/chatid` command
- Populate *settings.json* with your data as shown 
```
{
    "telegram_token": "your_token",
    "allowed_id": [
                   "your_chat_id",
                   "your_friend_chat_id,
                   "another_chat_id"
                  ],
    "insta_user": "your_username",
    "insta_pass": "your_password"
}
 ```
- To start the server launch `./main.py`
#### Write personal scripts 
- Edit `./scripts.py`
- Create a function with name as you preferred and put inside an InstaPy script, for example:
```python
def script_for_big_like(username, password, proxy):
    session = instapy.InstaPy(username=username, password=password)
    then put your instapy script.
```

### Avaiable commands
#### Jobs management
| Command  | Parameters                                | Description                                      |
|----------|-------------------------------------------|--------------------------------------------------|
| /set     | \<job_name\> \<script_name\> \<hh:mm\>    | Create a new schedule. Select the day from bot.  |
| /unset   | \<job_name\>                              | Delete a schedule.                               |
| /jobs    |                                           | Print all setted jobs                            |
| /scripts |                                           | Print all your scripts                           |
| /status  | \<job_name:optional\>                     | Print the status of all your thread or single.   |
| /now     | \<script_name\>                           | Run immediately.                                 |

