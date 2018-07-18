import datetime
import json

import gamedb
import datamodels


class PlayerData:
    def __init__(self):
        self.monster = None
        self.monster_stash = []

    def to_dict(self):
        return {
            'monster': self.monster.to_dict() if self.monster else '',
            'monster_stash': [i.to_dict() for i in self.monster_stash],
        }

    def save(self, file_object):
        data = self.to_dict()
        data['timestamp'] = datetime.datetime.now().isoformat(),
        json.dump(data, file_object, sort_keys=True)

    @classmethod
    def load(cls, file_object):
        gdb = gamedb.get_instance()
        player = cls()
        data = json.load(file_object)

        if data['monster']:
            player.monster = datamodels.Monster(data['monster'])
            player.monster.link(gdb)

        for monster in data['monster_stash']:
            monster = datamodels.Monster(monster)
            monster.link(gdb)
            player.monster_stash.append(monster)

        return player
