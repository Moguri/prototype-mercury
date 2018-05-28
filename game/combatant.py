import builtins

from direct.actor.Actor import Actor

import gamedb

class Combatant:
    def __init__(self, monster, parent_node, ability_inputs):
        gdb = gamedb.get_instance()

        self._monster = monster
        breed = monster.breed

        self.name = self._monster.name
        self.current_hp = self.max_hp
        self.current_ap = 20

        self.ability_inputs = ability_inputs
        self.abilities = [gdb['abilities'][ability_id] for ability_id in breed.abilities]

        self.range_index = 0
        self.target = None

        self.lock_controls = False

        if hasattr(builtins, 'base'):
            model = base.loader.load_model('{}.bam'.format(breed.bam_file))
            self.path = Actor(model.find('**/{}'.format(breed.root_node)))
            self.path.loop(self.get_anim('idle'))
            self.path.reparent_to(parent_node)
        else:
            self.path = Actor()


    def get_anim(self, anim):
        return self._monster.breed.anim_map[anim]

    @property
    def max_hp(self):
        return self._monster.hit_points

    @property
    def max_ap(self):
        return self._monster.ability_points

    @property
    def ap_per_second(self):
        return self._monster.ap_per_second

    @property
    def physical_attack(self):
        return self._monster.physical_attack

    @property
    def magical_attack(self):
        return self._monster.magical_attack

    @property
    def accuracy(self):
        return self._monster.accuracy

    @property
    def evasion(self):
        return self._monster.evasion

    @property
    def defense(self):
        return self._monster.defense

    @property
    def move_cost(self):
        return self._monster.move_cost

    def update(self, dt, range_index):
        self.range_index = range_index
        self.current_ap += self.ap_per_second * dt
        self.current_ap = min(self.current_ap, self.max_ap)

    def get_state(self):
        ability_labels = [
            base.event_mapper.get_labels_for_event(inp)[0]
            for inp in self.ability_inputs
        ]

        return {
            'name': self.name,
            'hp_current': self.current_hp,
            'hp_max': self.max_hp,
            'ap_current': int(self.current_ap),
            'ap_max': self.max_ap,
            'abilities': [{
                'name': ability.name,
                'input': _input.upper(),
                'range': ability.range,
                'cost': ability.cost,
                'usable': self.ability_is_usable(ability),
            } for ability, _input in zip(self.abilities, ability_labels)],
        }

    def ability_is_usable(self, ability):
        return (
            ability.cost < self.current_ap and
            self.range_index in ability.range and
            self.target is not None
        )
