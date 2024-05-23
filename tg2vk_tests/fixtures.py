import itertools
from dataclasses import dataclass
from operator import attrgetter
from typing import List

from tg2vk.config import Config
from tg2vk.database import model

config = Config(TG_BOT_TOKEN="BotToken", DB_URL="sqlite+aiosqlite:///", DEBUG=False)


@dataclass
class DbData:
    users: List[model.User]
    channels: List[model.Channel]
    reposts: List[model.RepostInfo]

    def __init__(self):
        self.users = [model.User(tg_id=index, lang="ru") for index in range(3)]
        self.channels = [model.Channel(channel_id=100 + index, title=f"Channel {index}")
                         for index in range(3)]
        self.reposts = [
            model.RepostInfo(channel=self.channels[0], user=self.users[0]),
            model.RepostInfo(channel=self.channels[0], user=self.users[0]),  # double!

            model.RepostInfo(channel=self.channels[1], user=self.users[1]),
            model.RepostInfo(channel=self.channels[1], user=self.users[0]),

            model.RepostInfo(channel=self.channels[2], user=self.users[0]),
            model.RepostInfo(channel=self.channels[2], user=self.users[2]),
            model.RepostInfo(channel=self.channels[2], user=self.users[0]),  # double!
        ]

    @property
    def all_data(self):
        return itertools.chain(self.users, self.channels, self.reposts)
