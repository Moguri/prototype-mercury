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

    def to_dict(self):
        return {
            prop: getattr(self, prop)
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
