import datetime
import json
import uuid

from . import gamedb
from .monster import Monster


class PlayerData:
    MAX_RANK = 4
    def __init__(self):
        self.name = 'Foo Man'
        self.monsters = []
        self.saveid = None
        self.last_save = datetime.datetime.now()
        self.personal_tags = set()
        self.rank = 1
        self.num_power_gems = 0

        self.newid()

    def newid(self):
        self.saveid = uuid.uuid4().hex

    def to_dict(self):
        return {
            'name': self.name,
            'saveid': self.saveid,
            'personal_tags': list(self.personal_tags),
            'rank': self.rank,
            'monsters': [i.to_dict(skip_extras=True) for i in self.monsters],
            'last_save': self.last_save.isoformat(),
            'num_power_gems': self.num_power_gems,
        }

    def can_use_form(self, form):
        return set(form.required_tags).issubset(self.personal_tags)

    @property
    def tags(self):
        return self.personal_tags | {
            f'rank_{i}' for i in range(self.rank+1)
        }

    def save(self, file_object):
        self.last_save = datetime.datetime.now()
        data = self.to_dict()
        json.dump(data, file_object, sort_keys=True)

    @classmethod
    def load(cls, file_object):
        gdb = gamedb.get_instance()
        player = cls()
        data = json.load(file_object)

        player.name = data['name']
        player.saveid = data['saveid']
        player.last_save = datetime.datetime.fromisoformat(data['last_save'])
        player.personal_tags = set(data['personal_tags'])
        player.rank = data['rank']
        player.num_power_gems = data['num_power_gems']
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
