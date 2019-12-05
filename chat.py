"""
nice -n 10 python3 chat.py
"""

import os
import sys
import time
import re
import random
import urllib
import json
import datetime
import pytz
import html

from urllib.request import urlopen

from quiz import Quiz

from slackclient import SlackClient
os.environ['SLACK_BOT_TOKEN'] = 'Secret slack token here'

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def random_gif():
    url = 'http://api.giphy.com/v1/gifs/search?api_key={api_key}&q=random&limit=1&offset={offset}&rating=pg-13'.format(
        api_key='<secret giphy api key here>' or os.environ.get('GIPHY_API_KEY'),
        offset=random.randint(0, 4000)
    )
    data = json.loads(urlopen(url).read().decode('utf8'))
    return data['data'][0]['images']['downsized']['url']

def random_emoji():
    with open(os.path.join(sys.path[0], 'emojis.txt')) as emoji_file:
        emojis = emoji_file.read()
    return random.choice(emojis)

def gif(inp):
    inp = inp.replace(' ', '-')
    url = 'http://api.giphy.com/v1/gifs/search?api_key={api_key}&q={query}&limit=1&offset={offset}&rating=pg-13'.format(
        api_key='<secret giphy api key here>' or os.environ.get('GIPHY_API_KEY'),
        offset=random.randint(1, 50),
        query=inp
    )
    data = json.loads(urlopen(url).read().decode('utf8'))
    return data['data'][0]['images']['downsized']['url']

def text(inp):
    return inp

def sixtynine():
    now = datetime.datetime.now(pytz.timezone('Europe/London'))
    if now.hour == 16 and now.minute == 51:
        return 'nice :sunglasses:'
    return 'Lol u missed it {}'.format(random_emoji())


QA = {
    'how are you|how goes it|hows it going': (
        random_emoji,
        gif,
        text,
        'not bad',
        'pretty good',
        'fantastic',
        'all right'
    ),
    'good morning|good afternoon|hello|hi|howdy|greetings|hey|wassup|wassup': (
        random_gif,
        text,
        'lo',
        'yo',
        'sup',
        'greetings mortal',
        'greets',
        'waddup',
        'what\'s happenin',
        'how goes it',
    ),
    'how do you do': (
        random_gif,
        text,
        'how do you do'
    ),
    'whats up|whats poppin|wag1|wagwan': (
        random_emoji,
        gif,
        text,
        'not much',
        'just chillin',
        'nagwan',
    ),
    'who are you|whats your name': (
        'bobby',
        'not tellin u',
        'i\'m a sheep',
    ),
    'female|male|guy|girl': (
        gif,
        text,
        'i\'m a robot',
        'yeah',
        'no',
        'kinda',
        'i\'m bobby'
    ),
    '69': sixtynine,
    'despacito': (
        'This is so sad :cry: https://www.youtube.com/watch?v=whwe0KD_rGw'
    ),
    'thanks|thank you|good job': (
        gif,
        text,
        'you\'re welcome',
        'whatever',
        'no problemo',
        'k',
        ':thumbsup:',
        ':pray:',
    ),
    ':hellyeah:': (
        'Please delete yourself',
        'Stop it',
        'I don\'t like that emoji'
    ),
    'random emoji': (random_emoji, text, 'no'),
    'random gif': (random_gif, text, 'no'),
    'random': (random_emoji, random_gif, text, 'no'),
}

DEFAULTS = (
    gif,
    random_emoji,
    lambda: gif('reaction'),
    text,
    'nope',
    'not tellin u nothin',
    'no idea what ur on about m8',
    'sure why not',
    'alright',
    'huh?',
    'mmm',
    'ok...',
    'so it has come to this',
    ':shrug:',
    'i have no idea what you\'re talkin about',
    'Not sure what you mean. Try yelling at your monitor.',
)

def matching_input(inp, keys):
    for key in keys.split('|'):
        k = key.replace(' ', '')
        if k.startswith(inp) or k.endswith(inp):
            return True

def form_answer(responses):
    if isinstance(responses, str):
        responses = (responses,)

    try:
        method = random.choice([x for x in responses if callable(x)])
    except TypeError:
        # is a single function on its own
        return responses()
    except (ValueError, IndexError):
        method = text

    try:
        string = random.choice([x for x in responses if not callable(x)])
    except IndexError:
        string = None

    if string:
        try:
            return method(string)
        except TypeError:
            pass

    return method()

def get_response(question):
    question = re.sub(r'\W+?', '', question).lower()
    for key in QA:
        if matching_input(question, key):
            return form_answer(QA[key])
    return form_answer(DEFAULTS)

# while True:
#     question = input('...')
#     print(get_response(question))


class Bobby(object):

    rtm_read_delay = 1
    mention_regex = '^<@(|[WU].+?)>(.*)'

    def __init__(self, client):
        self.client = client
        self.bot_id = client.api_call('auth.test')['user_id']
        self.quiz_mode = False
    #     self.users = self.get_users()

    # def get_users(self):
    #     users = self.client.api_call('users.list')
    #     return users['members']

    def get_username(self, user_id):
        return '<@{}>'.format(user_id)
        # for user in self.users:
        #     if user['id'] == user_id:
        #         return '@{}'.format(user['profile']['display_name'])
        # return ''

    def listen(self):
        user_id, command, channel = self.parse_bot_commands()
        if not command or not channel:
            return
        self.send_response(user_id, command, channel)
        time.sleep(self.rtm_read_delay)

    def parse_bot_commands(self):
        """
        Parses a list of events coming from the Slack RTM API to find bot
        commands. If a bot command is found, this function returns a tuple of
        command and channel. If its not found, then this function returns
        None, None.
        """
        for event in self.client.rtm_read():
            if event['type'] == 'message' and not 'subtype' in event:
                user_id, message = self.parse_direct_mention(event['text'])
                if user_id == self.bot_id:
                    return event['user'], message, event['channel']
        return '', '', ''

    def parse_direct_mention(self, message_text):
        """
        Finds a direct mention (a mention that is at the beginning) in message
        text and returns the user ID which was mentioned. If there is no direct
        mention, returns None.
        """
        matches = re.search(self.mention_regex, message_text)
        # the first group contains the username, the second group contains the
        # remaining message
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    def send_response(self, user_id, command, channel):
        """
        Executes bot command if the command is known
        """
        response = self.create_response(user_id, command)
        self.client.api_call(
            'chat.postMessage',
            channel=channel,
            text=response
        )

    def create_response(self, user_id, command):
        if command.lower() == 'start quiz':
            return self.start_quiz()
        elif command.lower() == 'end quiz':
            return self.end_quiz()
        elif self.quiz_mode:
            return self.get_quiz_response(user_id, command)
        else:
            return get_response(command)

    def start_quiz(self):
        self.quiz_mode = True
        self.quiz = Quiz(rounds=10)
        return self.quiz.current_question

    def end_quiz(self):
        self.quiz_mode = False
        self.quiz = None

    def get_quiz_response(self, user_id, command):
        r = self.quiz.make_attempt(self.get_username(user_id), command)
        if self.quiz.finished:
            self.end_quiz()
        return r

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        bobby = Bobby(slack_client)
        while True:
            bobby.listen()
            time.sleep(0.1)
    else:
        print('Connection failed. Exception traceback printed above.')
