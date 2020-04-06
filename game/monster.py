import builtins
import collections

from direct.actor.Actor import Actor
from direct.interval import IntervalGlobal as intervals

from . import gamedb


class MonsterActor:
    _anim_warnings = collections.defaultdict(set)

    def __init__(self, breed, parent_node=None):
        self.breed = breed

        if hasattr(builtins, 'base'):
            model = base.loader.load_model('{}.bam'.format(breed.bam_file))
            self._path = Actor(model.find('**/{}'.format(breed.root_node)))
            self.play_anim('idle', loop=True)
            if parent_node:
                self._path.reparent_to(parent_node)
        else:
            self._path = Actor()

    def __getattr__(self, name):
        return getattr(self._path, name)

    def __estattr__(self, name, value):
        return setattr(self._path, name, value)

    @property
    def as_nodepath(self):
        return self._path

    def _anim_warning(self, anim):
        if isinstance(anim, str):
            baseanim = anim
        else:
            baseanim = anim[-1]
        if baseanim not in self._anim_warnings[self.breed.id]:
            print(f'Warning: {self.breed.name} is missing an animation: {anim}')
            self._anim_warnings[self.breed.id].add(baseanim)

    def play_anim(self, anim, *, loop=False):
        self._path.stop()
        mapped_anim = self.get_anim(anim)
        if mapped_anim is None:
            self._anim_warning(anim)
            return
        if loop:
            self._path.loop(mapped_anim)
        else:
            self._path.play(mapped_anim)

    def get_anim(self, anims):
        if isinstance(anims, str):
            anims = [anims]

        for anim in anims:
            if anim in self._path.get_anim_names():
                return anim
            if anim in self.breed.anim_map:
                return self.breed.anim_map[anim]

        return None

    def actor_interval(self, anim):
        mapped_anim = self.get_anim(anim)
        if mapped_anim is None:
            self._anim_warning(anim)
            return intervals.Sequence()
        return self._path.actor_interval(mapped_anim)


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
        gdb = gamedb.get_instance()
        if name == 'hit_points':
            name = 'hp'
        if name in self.BASE_STATS:
            base_stat = getattr(self.breed, name)
            breed_contrib = getattr(self.breed, f'{name}_affinity') * self.level * 5
            job_contrib = 0
            for job, level in self.job_levels.items():
                job = gdb['jobs'][job]
                job_contrib += getattr(job, f'{name}_affinity') * level * 5
            return base_stat + breed_contrib + job_contrib
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

    def can_use_job(self, job):
        return set(job.required_tags).issubset(self.tags)

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

        return cls(monsterdata)

    @property
    def job(self):
        return self._monsterdata.job

    @job.setter
    def job(self, value):
        if not self.can_use_job(value):
            raise RuntimeError(f'tag requirements unsatisfied: {value.required_tags}')
        self._monsterdata.job = value
        if value.id not in self.job_levels:
            self.job_levels[value.id] = 1

    @property
    def ability_points(self):
        return 100

    @property
    def ap_per_second(self):
        return self.breed.ap_per_second

    @property
    def movement(self):
        return self.breed.movement

    @property
    def level(self):
        return sum(self.job_levels.values())

    @property
    def tags(self):
        return {
            f'breed_{self.breed.id}',
        } | {
            f'job_{jobname}_{joblevel}'
            for jobname, joblevel in self.job_levels.items()
        }
