import json

import gamedb
import datamodels


class PlayerData:
    def __init__(self):
        self.monster = None

    def to_dict(self):
        return {
            'monster': self.monster.to_dict() if self.monster else '',
        }

    def save(self, file_object):
        json.dump(self.to_dict(), file_object)

    @classmethod
    def load(cls, file_object):
        player = cls()
        data = json.load(file_object)

        if data['monster']:
            player.monster = datamodels.Monster(data['monster'])
            player.monster.link(gamedb.get_instance())

        return player
