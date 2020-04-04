import builtins

from direct.actor.Actor import Actor

from . import gamedb

class Combatant:
    def __init__(self, monster, parent_node):
        gdb = gamedb.get_instance()

        self._monster = monster
        breed = monster.breed

        self.current_hp = self.max_hp
        self.current_ap = 20

        self.abilities = [gdb['abilities'][ability_id] for ability_id in monster.job.abilities]

        self.range_index = 0
        self.target = None
        self.tile_position = (0, 0)

        self.lock_controls = False

        if hasattr(builtins, 'base'):
            model = base.loader.load_model('{}.bam'.format(breed.bam_file))
            self.path = Actor(model.find('**/{}'.format(breed.root_node)))
            self.play_anim('idle', loop=True)
            self.path.reparent_to(parent_node)
        else:
            self.path = Actor()

    def __getattr__(self, name):
        return getattr(self._monster, name)

    def play_anim(self, anim, *, loop=False):
        self.path.stop()
        anim = self.get_anim(anim)
        if loop:
            self.path.loop(anim)
        else:
            self.path.play(anim)

    def get_anim(self, anim):
        return self._monster.breed.anim_map[anim]

    @property
    def max_hp(self):
        return self._monster.hit_points

    @property
    def is_dead(self):
        return self.current_hp <= 0

    @property
    def max_ap(self):
        return self._monster.ability_points

    def update(self, dt, range_index):
        self.range_index = range_index
        self.current_ap += self.ap_per_second * dt
        self.current_ap = min(self.current_ap, self.max_ap)

    def get_state(self):
        return {
            'name': self.name,
            'hp_current': self.current_hp,
            'hp_max': self.max_hp,
        }

    def ability_is_usable(self, ability):
        return (
            ability.cost < self.current_ap and
            self.range_index in ability.range and
            self.target is not None
        )
