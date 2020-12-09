import builtins
import collections
import random

import panda3d.core as p3d
from direct.actor.Actor import Actor
from direct.interval import IntervalGlobal as intervals

from . import gamedb
from . import effects


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
        if isinstance(weapon,str):
            gdb = gamedb.get_instance()
            weapon = gdb['weapons'][weapon]

        meshname = weapon.mesh['root_node']
        if meshname == '':
            return
        weapon_joint = self._path.expose_joint(None, 'modelRoot', 'weapon')
        modelroot = base.loader.load_model('models/{}.bam'.format(weapon.mesh['bam_file']))
        mesh = modelroot.find(f'**/{meshname}')
        if mesh.is_empty():
            print(f'Warning: could not find weapon {meshname}')
            modelroot.ls()
            return
        elif weapon_joint is None:
            print(f'Warning: could not find weapon joint on {self.form.name}')
            return

        # Update weapon transform
        weaponxf = self.form.weapon_offset
        def __scale_down__(array):
            array[0] = array[0] * .1
            array[1] = array[1] * .1
            array[2] = array[2] * .1
            return array
        pos, hpr, scale = weaponxf['position'][:], weaponxf['hpr'][:], weaponxf['scale'][:]
        pos = __scale_down__(pos)
        pos[1] += 0.4
        mesh.set_pos(mesh.get_pos() + p3d.LVector3(*pos))
        mesh.set_hpr(*hpr)
        scale = [
            scale[idx] / inv
            for idx, inv in enumerate(weapon_joint.get_scale())
        ]
        mesh.set_scale(*scale)
        mesh.instance_to(weapon_joint)

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
    MAX_POWER = 6
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
            'power_spent',
        ] + self.BASE_STATS
        data.update({
            prop: getattr(self, prop)
            for prop in extras
        })
        data['form'] = self.form.to_dict()
        if self.weapon is not None:
            data['weapon'] = self.weapon.to_dict()

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
            'weapon': 'unarmed'
        })
        monsterdata.link(gdb)

        monster = cls(monsterdata)
        return monster

    @property
    def weapon(self):
        return self._monsterdata.weapon

    @weapon.setter
    def weapon(self, value):
        if value is None:
            value = 'unarmed'

        if isinstance(value, str):
            gdb = gamedb.get_instance()
            value = gdb['weapons'][value]

        self._monsterdata.abilities_learned_weapon = []
        self._monsterdata.weapon = value

    @classmethod
    def gen_random(cls, monsterid, _level):
        gdb = gamedb.get_instance()
        mon = cls.make_new(monsterid)
        mon.weapon = random.choice(list(gdb['weapons'].values()))
        return mon

    @property
    def tags(self):
        return {
            f'form_{self.form.id}',
        } | set(self.form.tags)

    @property
    def abilities(self):
        def filter_abilities(abilities, learned_list):
            return [
                ability
                for ability in abilities
                if ability.id in learned_list
            ]
        return (
            filter_abilities(self.weapon.abilities, self.abilities_learned_weapon)
            + filter_abilities(self.form.abilities, self.abilities_learned_form)
        )

    def upgrades_for_stat(self, stat):
        total = 0
        for ability in self.abilities:
            for passive in ability.passives:
                if passive['type'] == 'change_stat' and passive['parameters']['stat'] == stat:
                    incr = effects.calculate_strength(self, ability)
                    total += incr

        return total

    @property
    def power_available(self):
        return self._monsterdata.power_available

    @power_available.setter
    def power_available(self, value):
        self._monsterdata.power_available = value

    @property
    def power_spent(self):
        return (
            len(self._monsterdata.abilities_learned_weapon)
            + len(self._monsterdata.abilities_learned_form)
        )

    def can_use_weapon(self, weapon, extra_tags=None):
        if extra_tags is None:
            extra_tags = set()
        return set(weapon.required_tags).issubset(self.tags | extra_tags)
