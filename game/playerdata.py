import datetime
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
        data = self.to_dict()
        data['timestamp'] = datetime.datetime.now().isoformat(),
        json.dump(data, file_object, sort_keys=True)

    @classmethod
    def load(cls, file_object):
        player = cls()
        data = json.load(file_object)

        if data['monster']:
            player.monster = datamodels.Monster(data['monster'])
            player.monster.link(gamedb.get_instance())

        return player