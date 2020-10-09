import random

from .monster import MonsterActor
from . import effects

class Combatant:
    def __init__(self, monster, parent_node):
        self._monster = monster
        form = monster.form

        self._current_hp = self.max_hp
        self.current_ep = self.max_ep
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
    def max_ep(self):
        return self._monster.ep

    @property
    def is_dead(self):
        return self.current_hp <= 0

    def get_state(self):
        return {
            'name': self.name,
            'hp_current': self.current_hp,
            'hp_max': self.max_hp,
            'ep_current': self.current_ep,
            'ep_max': self.max_ep,
            'ct_current': min(100, self.current_ct),
            'ct_max': 100,
        }

    def use_ability(self, ability, target, controller, effect_node):
        controller.display_message(
            f'{self.name} is using {ability.name} '
            f'on {target.name}'
        )

        self.current_ep -= ability.ep_cost
        self.target = target
        target.target = self

        self.ability_used = True

        return effects.sequence_from_ability(
            effect_node,
            self,
            ability,
            controller
        )

    def rest(self):
        self.current_ep = self.max_ep

    def can_move(self):
        return self.move_current > 0 and self.current_ep > 0

    def can_rest(self):
        return self.move_current == self.move_max and not self.ability_used

    def can_use_ability(self, ability):
        if self.ability_used:
            return False
        return ability.ep_cost <= self.current_ep
