import datetime
import json
import uuid

import gamedb
import datamodels


class PlayerData:
    def __init__(self):
        self.name = 'FooMan'
        self.monster = None
        self.monster_stash = []
        self.saveid = ''

        self.new_saveid()

    def to_dict(self):
        return {
            'name': self.name,
            'monster': self.monster.to_dict() if self.monster else '',
            'monster_stash': [i.to_dict() for i in self.monster_stash],
        }

    def to_meta_dict(self):
        return {
            'id': self.saveid,
            'trainer_name': self.name,
            'monster_name': self.monster.name if self.monster else '',
            'monster_breed_name': self.monster.breed.name if self.monster else '',
            'last_access_time': datetime.datetime.now().isoformat(),
        }


    def new_saveid(self):
        self.saveid = uuid.uuid1().hex

    def save(self, file_object):
        data = self.to_dict()
        json.dump(data, file_object, sort_keys=True)

    @classmethod
    def load(cls, file_object):
        gdb = gamedb.get_instance()
        player = cls()
        data = json.load(file_object)

        player.name = str(data['name'])

        if data['monster']:
            player.monster = datamodels.Monster(data['monster'])
            player.monster.link(gdb)

        for monster in data['monster_stash']:
            monster = datamodels.Monster(monster)
            monster.link(gdb)
            player.monster_stash.append(monster)

        return player
