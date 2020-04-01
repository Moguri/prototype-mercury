from . import gamedb


class Monster:
    BASE_STATS = [
        'hp',
        'physical_attack',
        'magical_attack',
        'accuracy',
        'evasion',
        'defense',
    ]
    def __init__(self, monsterdata):
        self._monsterdata = monsterdata

    def __getattr__(self, name):
        if name == 'hit_points':
            name = 'hp'
        if name in self.BASE_STATS:
            return getattr(self.breed, name) + getattr(self._monsterdata, f'{name}_offset')
        return getattr(self._monsterdata, name)

    def to_dict(self, skip_extras=False):
        data = self._monsterdata.to_dict()
        if skip_extras:
            return data

        extras = [
            'hit_points',
            'ability_points',
        ] + self.BASE_STATS
        data.update({
            prop: getattr(self, prop)
            for prop in extras
        })

        return data

    @classmethod
    def make_new(cls, monster_id, name, breed_id):
        gdb = gamedb.get_instance()

        breed = gdb['breeds'][breed_id]
        monsterdata = gdb.schema_to_datamodel['monsters']({
            'id': monster_id,
            'name': name,
            'breed': breed.id,
            'job': breed.default_job.id,
            'job_levels': {
                breed.default_job.id: 1,
            }
        })
        monsterdata.link(gdb)
        gdb['monsters'][monster_id] = monsterdata

        return cls(monsterdata)

    @property
    def job(self):
        return self._monsterdata.job

    @job.setter
    def job(self, value):
        self._monsterdata.job = value

    @property
    def ability_points(self):
        return 100

    @property
    def ap_per_second(self):
        return self.breed.ap_per_second

    @property
    def move_cost(self):
        return self.breed.move_cost

    @property
    def level(self):
        return sum(self.job_levels.values())
