import os
import sys
import time
import re
import random
import urllib
import json
from urllib.request import urlopen
from slackclient import SlackClient

os.environ['SLACK_BOT_TOKEN'] = 'Secret key here'
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


class Bobby(object):

    rtm_read_delay = 1
    mention_regex = '^<@(|[WU].+?)>(.*)'
    default_response = 'Not sure what you mean. Try yelling at your monitor.'

    def __init__(self, client):
        self.client = client
        self.bot_id = client.api_call('auth.test')['user_id']

    def listen(self):
        command, channel = self.parse_bot_commands()
        self.send_response(command, channel)
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
                    return message, event['channel']
        return '', ''

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

    def send_response(self, command, channel):
        """
        Executes bot command if the command is known
        """
        response = self.create_response(command)
        self.client.api_call(
            'chat.postMessage',
            channel=channel,
            text=response
        )

    def create_response(self, command):
        if command.lower().startswith('tell'):
            person_name = command.split(' ')[1].lower()
            message_to_tell = ' '.join(command.split(' ')[2:])
            if person_name in ['hector', 'irina']:
                return '{} is pretty cool imo'.format(person_name.title())
            return '{} {}'.format(person_name.title(), message_to_tell)
        if 'random emoji' in command.lower():
            return self.random_emoji()
        if command == '69':
            return self.sixty_nine()
        if 'play despacito' in command.lower():
            return self.play_despacito()
        if 'random gif' in command.lower():
            return self.random_gif()
        if 'thank' in command.lower():
            return self.search_gif("you're-welcome")
        return self.default_response

    def random_emoji(self):
        with open(os.path.join(sys.path[0], 'emojis.txt')) as emoji_file:
            emojis = emoji_file.read()
        return random.choice(emojis)

    def sixty_nine(self):
        return 'nice :sunglasses:'

    def play_despacito(self):
        return 'This is so sad https://www.youtube.com/watch?v=whwe0KD_rGw'

    def random_gif(self):
        url = 'http://api.giphy.com/v1/gifs/search?api_key={api_key}&q=random&limit=1&offset={offset}&rating=pg-13'.format(
            api_key='kiW9bKPcKfuRiMYILAskeS8JRwAOAWDb' or os.environ.get('GIPHY_API_KEY'),
            offset=random.randint(0, 4000)
        )
        data = json.loads(urlopen(url).read().decode('utf8'))
        return data['data'][0]['images']['downsized']['url']

    def search_gif(self, search_term):
        url = 'http://api.giphy.com/v1/gifs/search?api_key={api_key}&q={query}&limit=1&offset={offset}&rating=pg-13'.format(
            api_key='kiW9bKPcKfuRiMYILAskeS8JRwAOAWDb' or os.environ.get('GIPHY_API_KEY'),
            offset=random.randint(1, 6),
            query=search_term
        )
        print(url)
        data = json.loads(urlopen(url).read().decode('utf8'))
        return data['data'][0]['images']['downsized']['url']

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        bobby = Bobby(slack_client)
        while True:
            bobby.listen()
    else:
        print('Connection failed. Exception traceback printed above.')
