class Monster:
    def __init__(self, monsterdata):
        self._monsterdata = monsterdata

    def __getattr__(self, name):
        return getattr(self._monsterdata, name)

    def to_dict(self):
        data = self._monsterdata.to_dict()
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
        return self.breed.hp + self._monsterdata.hp_offset

    @property
    def ability_points(self):
        return 100

    @property
    def ap_per_second(self):
        return self.breed.ap_per_second

    @property
    def physical_attack(self):
        return self.breed.physical_attack + self._monsterdata.physical_attack_offset

    @property
    def magical_attack(self):
        return self.breed.magical_attack + self._monsterdata.magical_attack_offset

    @property
    def accuracy(self):
        return self.breed.accuracy + self._monsterdata.accuracy_offset

    @property
    def evasion(self):
        return self.breed.evasion + self._monsterdata.evasion_offset

    @property
    def defense(self):
        return self.breed.defense + self._monsterdata.defense_offset

    @property
    def move_cost(self):
        return self.breed.move_cost
