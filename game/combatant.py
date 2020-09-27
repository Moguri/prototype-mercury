import random

from .monster import MonsterActor

class Combatant:
    def __init__(self, monster, parent_node):
        self._monster = monster
        form = monster.form

        self._current_hp = self.max_hp
        self.current_mp = self.max_mp
        self.current_ct = random.randrange(0, 10)
        self.move_max = self.movement
        self.move_current = 0
        self.ability_used = False

        self.abilities = [
            monster.job.basic_attack
        ] + monster.abilities

        self.range_index = 0
        self.target = None
        self.tile_position = (0, 0)

        self.lock_controls = False

        self._actor = MonsterActor(form, parent_node, monster.job.id)

    def __getattr__(self, name):
        if hasattr(self._monster, name):
            return getattr(self._monster, name)
        return getattr(self._actor, name)

    @property
    def current_hp(self):
        return self._current_hp

    @current_hp.setter
    def current_hp(self, value):
        wasdead = self.is_dead
        self._current_hp = value
        if not wasdead and self.is_dead:
            self.play_anim('death')

    @property
    def max_hp(self):
        return self._monster.hit_points

    @property
    def max_mp(self):
        return self._monster.mp

    @property
    def is_dead(self):
        return self.current_hp <= 0

    def get_state(self):
        return {
            'name': self.name,
            'hp_current': self.current_hp,
            'hp_max': self.max_hp,
            'mp_current': self.current_mp,
            'mp_max': self.max_mp,
            'ct_current': min(100, self.current_ct),
            'ct_max': 100,
        }
