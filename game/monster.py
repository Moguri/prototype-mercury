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
    _WEAPONS_FILE = 'models/weapons.bam'

    def __init__(self, form, parent_node=None, weapon=None):
        self.form = form

        mesh = self.form.mesh

        if hasattr(builtins, 'base'):
            if self._ANIMS is None:
                anim_root = base.loader.load_model(self._ANIM_FILE)
                self.__class__._ANIMS = p3d.NodePath('anims')
                for bundle in anim_root.find_all_matches('**/+AnimBundleNode'):
                    bundle.reparent_to(self._ANIMS)
            model = base.loader.load_model('models/{}.bam'.format(mesh['bam_file']))
            root_node = model.find('**/{}'.format(mesh['root_node']))
            if root_node.is_empty():
                print(
                    f"Warning: root node ({mesh['root_node']}) not found in "
                    f"bam_file ({mesh['bam_file']}) for {form.id}"
                )
            else:
                self._ANIMS.instance_to(root_node)
            self._path = Actor(root_node)
            if weapon:
                self.update_weapon(weapon)
            self.play_anim('idle', loop=True)
            if parent_node:
                self._path.reparent_to(parent_node)
        else:
            self._path = Actor()

    def update_weapon(self, weapon):
        weapon_joint = self._path.expose_joint(None, 'modelRoot', 'weapon')
        weapons = base.loader.load_model(self._WEAPONS_FILE)
        weapon = weapons.find(f'**/{weapon}')
        if weapon.is_empty():
            print(f'Warning: could not find weapon {weapon}')
            weapons.ls()
        else:
            weapon.set_y(0.4)
            inv_scale = [1 / i for i in weapon_joint.get_scale()]
            weapon.set_scale(*inv_scale)
            weapon.instance_to(weapon_joint)

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
    BASE_STATS = [
        'hp',
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
            return base_stat + upgrades_contrib
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
        })
        monsterdata.link(gdb)

        monster = cls(monsterdata)
        return monster

    @classmethod
    def gen_random(cls, monsterid, _level):
        mon = cls.make_new(monsterid)
        return mon

    @property
    def tags(self):
        return {
            f'form_{self.form.id}',
        } | set(self.form.tags)

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
