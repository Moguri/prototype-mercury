#pylint: disable=attribute-defined-outside-init

import pprint


class DataModel:
    _props = []

    def __init__(self, dict_data):
        self._props |= {'id', 'name'}
        for prop in self._props:
            setattr(self, prop, dict_data[prop])

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            pprint.pformat(self.__dict__)
        )

    def link(self, _gdb):
        pass

    def to_dict(self):
        def _ga(prop):
            return getattr(self, prop)

        return {
            prop: _ga(prop).id if isinstance(_ga(prop), DataModel) else _ga(prop)
            for prop in self._props
        }


class Ability(DataModel):
    _props = {
        'cost',
        'range',
        'damage_rank',
        'hit_rank',
        'type',
        'effects',
    }


class Breed(DataModel):
    _props = {
        'bam_file',
        'root_node',
        'anim_map',
        'abilities',
        'hp',
        'ap_per_second',
        'physical_attack',
        'magical_attack',
        'defense',
        'evasion',
        'accuracy',
        'move_cost',
    }


class Monster(DataModel):
    _props = {
        'breed',
        'hp_offset',
        'ap_offset',
        'physical_attack_offset',
        'magical_attack_offset',
        'accuracy_offset',
        'evasion_offset',
        'defense_offset',
    }

    def link(self, gdb):
        self.breed = gdb['breeds'][self.breed]

    def to_dict(self):
        data = super().to_dict()
        extras = [
            'hit_points',
            'ability_points',
            'physical_attack',
            'magical_attack',
            'accuracy',
            'evasion',
            'defense',
        ]
        data.update({
            prop: getattr(self, prop)
            for prop in extras
        })

        return data

    @property
    def hit_points(self):
        return self.breed.hp + self.hp_offset

    @property
    def ability_points(self):
        return 100

    @property
    def ap_per_second(self):
        return self.breed.ap_per_second

    @property
    def physical_attack(self):
        return self.breed.physical_attack + self.physical_attack_offset

    @property
    def magical_attack(self):
        return self.breed.magical_attack + self.magical_attack_offset

    @property
    def accuracy(self):
        return self.breed.accuracy + self.accuracy_offset

    @property
    def evasion(self):
        return self.breed.evasion + self.evasion_offset

    @property
    def defense(self):
        return self.breed.defense + self.defense_offset

    @property
    def move_cost(self):
        return self.breed.move_cost
