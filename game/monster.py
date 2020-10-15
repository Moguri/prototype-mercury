import builtins
import collections
import random

import panda3d.core as p3d
from direct.actor.Actor import Actor
from direct.interval import IntervalGlobal as intervals

from . import gamedb


RANDOM_NAMES = [
    'Aeon Faunagrief',
    'Aeon Valentine',
    'Bedlam Gunner',
    'Belladonna Griefamber',
    'Honor Mourner',
    'Hunter Seraphslayer',
    'Maxim Jester',
    'Maxim Veil',
    'Rage Darkdawn',
    'Raven Grimhunter',
    'Reaper Queenbane',
    'Seraph Ravendragon',
    'Solitaire Knight',
    'Song Darkwarden',
    'Spirit Griffon',
    'Spirit Mistangel',
    'Star Saber',
    'Totem Beastguard',
    'Wolf Steeltotem',
    'Zealot Talon',
]


class MonsterActor:
    _anim_warnings = collections.defaultdict(set)
    _ANIMS = None
    _ANIM_FILE = 'models/golem_animations.bam'

    def __init__(self, form, parent_node=None, job=None):
        self.form = form

        if job not in self.form.skins:
            job = 'default'
        skin = self.form.skins[job]

        if self._ANIMS is None:
            anim_root = base.loader.load_model(self._ANIM_FILE)
            self.__class__._ANIMS = p3d.NodePath('anims')
            for bundle in anim_root.find_all_matches('**/+AnimBundleNode'):
                bundle.reparent_to(self._ANIMS)

        if hasattr(builtins, 'base'):
            model = base.loader.load_model('models/{}.bam'.format(skin['bam_file']))
            root_node = model.find('**/{}'.format(skin['root_node']))
            if root_node.is_empty():
                print(
                    f"Warning: root node ({skin['root_node']}) not found in "
                    f"bam_file ({skin['bam_file']}) for {form.id}/{job}"
                )
            else:
                self._ANIMS.instance_to(root_node)
            self._path = Actor(root_node)
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
        if baseanim not in self._anim_warnings[self.form.id]:
            print(f'Warning: {self.form.name} is missing an animation: {anim}')
            self._anim_warnings[self.form.id].add(baseanim)

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
            if anim in self.form.anim_map:
                return self.form.anim_map[anim]

        return None

    def actor_interval(self, anim):
        mapped_anim = self.get_anim(anim)
        if mapped_anim is None:
            self._anim_warning(anim)
            return intervals.Sequence()
        return self._path.actor_interval(mapped_anim)


class Monster:
    JP_PER_LEVEL = 200

    STAT_UPGRADE_COST = 100

    BASE_STATS = [
        'hp',
        'ep',
        'physical_attack',
        'magical_attack',
        'movement',
    ]
    def __init__(self, monsterdata):
        self._monsterdata = monsterdata

    def __getattr__(self, name):
        if name == 'hit_points':
            name = 'hp'
        if name in self.BASE_STATS:
            base_stat = getattr(self.form, name)
            upgrades_contrib = self.upgrades_for_stat(name)
            jobs_contrib = getattr(self.job, f'{name}_offset')
            return base_stat + upgrades_contrib + jobs_contrib
        return getattr(self._monsterdata, name)

    def to_dict(self, skip_extras=False):
        data = self._monsterdata.to_dict()
        if skip_extras:
            return data

        extras = [
            'hit_points',
        ] + self.BASE_STATS
        data.update({
            prop: getattr(self, prop)
            for prop in extras
        })

        return data

    def can_use_job(self, job):
        return f'job_{job.id}' in self.tags or set(job.required_tags).issubset(self.tags)

    @classmethod
    def get_random_name(cls):
        return random.choice(RANDOM_NAMES)

    @classmethod
    def make_new(cls, monster_id, name=None, form_id=None):
        gdb = gamedb.get_instance()

        if name is None:
            name = cls.get_random_name()

        if form_id is not None:
            form = gdb['forms'][form_id]
        else:
            form = random.choice([
                i for i in gdb['forms'].values()
                if not set(i.required_tags) & {'disabled', 'in_test'}
            ])

        monsterdata = gdb.schema_to_datamodel['monsters']({
            'id': monster_id,
            'name': name,
            'form': form.id,
            'job': form.default_job.id,
        })
        monsterdata.link(gdb)

        monster = cls(monsterdata)
        for job in monster.available_jobs:
            monster.add_jp(job, 100)
        return monster

    @classmethod
    def gen_random(cls, monsterid, level):
        gdb = gamedb.get_instance()
        mon = cls.make_new(monsterid)

        while mon.level < level:
            job = random.choice(mon.available_jobs)
            mon.add_jp(job, cls.JP_PER_LEVEL)

        def get_abilities(job):
            jp_unspent = mon.jp_unspent.get(job.id, 0)
            def allow_ability(ability):
                return (
                    ability not in mon.abilities and
                    ability.jp_cost <= jp_unspent
                )
            return [
                ability
                for ability in (gdb['abilities'][i] for i in mon.job.abilities)
                if allow_ability(ability)
            ]

        for job in mon.available_jobs:
            mon.job = job
            available_abilities = get_abilities(job)
            while available_abilities:
                ability = random.choice(available_abilities)
                mon.add_ability(ability)
                available_abilities = get_abilities(job)

        mon.job = random.choice(mon.available_jobs)
        return mon

    @property
    def job(self):
        return self._monsterdata.job

    @job.setter
    def job(self, value):
        if not self.can_use_job(value):
            raise RuntimeError(f'tag requirements unsatisfied: {value.required_tags}')
        self._monsterdata.job = value

    @property
    def jp_spent(self):
        gdb = gamedb.get_instance()
        return {
            jobid: sum([gdb['abilities'][abid].jp_cost for abid in abilities])
            for jobid, abilities in self._monsterdata.abilities.items()
        }

    @property
    def jp_totals(self):
        return {
            jobid: unspent + self.jp_spent.get(jobid, 0)
            for jobid, unspent in self.jp_unspent.items()
        }

    def job_level(self, job):
        if not isinstance(job, str):
            job = job.id
        totjp = self.jp_totals.get(job, 0)
        return 1 + totjp // self.JP_PER_LEVEL

    def add_jp(self, job, value):
        if not isinstance(job, str):
            job = job.id
        if job in self.jp_unspent:
            self.jp_unspent[job] += value
        else:
            self.jp_unspent[job] = value

    @property
    def level(self):
        return 1 + sum((self.job_level(i) - 1 for i in self.jp_totals))

    @property
    def available_jobs(self):
        gdb = gamedb.get_instance()
        return [
            job
            for job in gdb['jobs'].values()
            if self.can_use_job(job)
        ]

    @property
    def tags(self):
        return {
            f'form_{self.form.id}',
        } | {
            f'job_{job}_{level}'
            for job in self.jp_unspent
            for level in range(1, self.job_level(job) + 1)
        } | set(self.form.tags)

    def add_ability(self, ability):
        if isinstance(ability, str):
            gdb = gamedb.get_instance()
            ability = gdb['abilities'][ability]
        if self.job.id not in self.jp_unspent:
            self._monsterdata.jp_unspent[self.job.id] = 0
        self._monsterdata.jp_unspent[self.job.id] -= ability.jp_cost
        if self.job.id not in self._monsterdata.abilities:
            self._monsterdata.abilities[self.job.id] = []
        self._monsterdata.abilities[self.job.id].append(ability.id)

    @property
    def abilities(self):
        gdb = gamedb.get_instance()
        return [
            gdb['abilities'][abid]
            for ablist in self._monsterdata.abilities.values()
            for abid in ablist
        ]

    def upgrades_for_stat(self, stat):
        return sum([
            upgrades.get(stat, 0)
            for upgrades in self.stat_upgrades.values()
        ])

    def upgrade_stat(self, stat):
        job = self.job.id
        if job not in self.jp_unspent:
            self._monsterdata.jp_unspent[job] = 0
        self.jp_unspent[job] -= self.STAT_UPGRADE_COST
        if job not in self.stat_upgrades:
            self.stat_upgrades[job] = {}
        if stat not in self.stat_upgrades[job]:
            self.stat_upgrades[job][stat] = 0
        self.stat_upgrades[job][stat] += 1
