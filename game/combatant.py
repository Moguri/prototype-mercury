from . import gamedb
from .monster import MonsterActor

class Combatant:
    def __init__(self, monster, parent_node):
        gdb = gamedb.get_instance()

        self._monster = monster
        breed = monster.breed

        self.current_hp = self.max_hp
        self.current_ct = 0
        self.move_max = self.movement
        self.move_current = 0

        self.abilities = [gdb['abilities'][ability_id] for ability_id in monster.job.abilities]

        self.range_index = 0
        self.target = None
        self.tile_position = (0, 0)

        self.lock_controls = False

        self._actor = MonsterActor(breed, parent_node)

    def __getattr__(self, name):
        if hasattr(self._monster, name):
            return getattr(self._monster, name)
        return getattr(self._actor, name)

    @property
    def max_hp(self):
        return self._monster.hit_points

    @property
    def is_dead(self):
        return self.current_hp <= 0

    def get_state(self):
        return {
            'name': self.name,
            'hp_current': self.current_hp,
            'hp_max': self.max_hp,
            'ct_current': min(100, self.current_ct),
            'ct_max': 100,
        }
