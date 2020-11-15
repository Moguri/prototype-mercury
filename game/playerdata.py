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
        self.personal_tags = set()
        self.rank = 1

    def to_dict(self):
        return {
            'name': self.name,
            'saveid': self.saveid,
            'personal_tags': list(self.personal_tags),
            'rank': self.rank,
            'monsters': [i.to_dict(skip_extras=True) for i in self.monsters],
            'last_access_time': self.last_access_time,
        }

    def can_use_form(self, form):
        return set(form.required_tags).issubset(self.personal_tags)

    @property
    def tags(self):
        return self.personal_tags | {
            tag for monster in self.monsters for tag in monster.tags
        } | {
            f'rank_{i}' for i in range(self.rank+1)
        }

    def save(self, file_object):
        data = self.to_dict()
        json.dump(data, file_object, sort_keys=True)

    @classmethod
    def load(cls, file_object):
        gdb = gamedb.get_instance()
        player = cls()
        data = json.load(file_object)

        player.name = data['name']
        player.saveid = data['saveid']
        player.personal_tags = set(data['personal_tags'])
        player.rank = data['rank']
        for monster_data in data['monsters']:
            monster = gdb.schema_to_datamodel['monsters'](monster_data)
            monster.link(gdb)
            player.monsters.append(Monster(monster))

        return player

    @property
    def max_monsters(self):
        return {
            1: 2,
            2: 3,
            3: 5,
            4: 8,
        }[self.rank]
