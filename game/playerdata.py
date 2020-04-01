import datetime
import json
import uuid

from . import gamedb
from .monster import Monster


class PlayerData:
    def __init__(self):
        self.name = 'Foo Man'
        self.monsters = []
        self.saveid = uuid.uuid4().hex
        self.last_access_time = datetime.datetime.now().isoformat()

    def to_dict(self):
        return {
            'name': self.name,
            'saveid': self.saveid,
            'monsters': [i.to_dict(skip_extras=True) for i in self.monsters],
            'last_access_time': self.last_access_time,
        }

    def to_metadata_dict(self):
        return {
            'id': self.saveid,
            'trainer_name': self.name,
            'last_access_time': self.last_access_time,
        }

    def save(self, file_object):
        data = self.to_dict()
        json.dump(data, file_object, sort_keys=True)

    @classmethod
    def load(cls, file_object):
        gdb = gamedb.get_instance()
        player = cls()
        data = json.load(file_object)

        player.name = str(data['name'])
        for monster_data in data['monsters']:
            monster = gdb.schema_to_datamodel['monsters'](monster_data)
            monster.link(gdb)
            player.monsters.append(Monster(monster))

        return player
