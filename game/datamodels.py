import pprint


class DataModel:
    _props = []

    def __init__(self, dict_data):
        for prop in self._props:
            setattr(self, prop, dict_data[prop])

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            pprint.pformat(self.__dict__)
        )


class Ability(DataModel):
    _props = [
        'id',
        'name',
        'cost',
        'range',
        'damage_rank',
        'hit_rank',
        'type',
        'effects',
    ]


class Breed(DataModel):
    _props = [
        'id',
        'name',
        'bam_file',
        'root_node',
        'anim_map',
        'hp',
        'ap_per_second',
        'physical_attack',
        'magical_attack',
        'defense',
        'evasion',
        'accuracy',
        'move_cost',
    ]
