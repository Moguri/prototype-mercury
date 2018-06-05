import random

from direct.actor.Actor import Actor
import panda3d.core as p3d

import gamedb

from .gamestate import GameState


class RanchState(GameState):
    def __init__(self):
        super().__init__()

        gdb = gamedb.get_instance()
        self.player = base.blackboard['player']

        # Make sure the player has a monster
        if self.player.monster is None:
            # Assign a random Monster for now. In the future, we will
            # present a monster selection screen
            self.player.monster = random.choice(list(gdb['monsters'].values()))
            print("Assigned monster: {}".format(self.player.monster.name))

        # Load and display the monster model
        breed = self.player.monster.breed
        monster_model = base.loader.load_model('{}.bam'.format(breed.bam_file))
        self.monster_actor = Actor(monster_model.find('**/{}'.format(breed.root_node)))
        self.monster_actor.set_h(180)
        self.monster_actor.loop(breed.anim_map['idle'])
        self.monster_actor.reparent_to(self.root_node)

        # Setup lighting
        self.light = p3d.DirectionalLight('dlight')
        self.lightnp = self.root_node.attach_new_node(self.light)
        self.lightnp.set_pos(2, -4, 4)
        self.lightnp.look_at(0, 0, 0)
        self.root_node.set_light(self.lightnp)

        # Setup Camera
        base.camera.set_pos(-3, -5, 5)
        base.camera.look_at(0, 0, 1)

        # UI
        self.menus = {
            'base': [
                ('Combat', self.enter_combat, []),
                ('Train', self.set_menu, ['training']),
            ],
            'training': [
                ('Back', self.set_menu, ['base']),
                ('Hit Points', self.train_stat, ['hp']),
                ('Physical Attack', self.train_stat, ['physical_attack']),
                ('Magical Attack', self.train_stat, ['magical_attack']),
                ('Accuracy', self.train_stat, ['accuracy']),
                ('Evasion', self.train_stat, ['evasion']),
                ('Defense', self.train_stat, ['defense']),
            ],
        }
        self.menu_items = None
        self.selection_idx = 0
        self.set_menu('base')

        self.accept('p1-move-down', self.increment_selection)
        self.accept('p1-move-up', self.decrement_selection)
        self.accept('p1-accept', self.accept_selection)
        self.accept('p1-reject', self.set_menu, ['base'])

        self.load_ui('ranch')
        self.update_ui({
            'menu_items': [i[0] for i in self.menu_items],
        })

    def update(self, dt):
        super().update(dt)

        self.update_ui({
            'selection_index': self.selection_idx,
        })

    def increment_selection(self):
        self.selection_idx += 1
        if self.selection_idx >= len(self.menu_items):
            self.selection_idx = 0

    def decrement_selection(self):
        self.selection_idx -= 1
        if self.selection_idx < 0:
            self.selection_idx = len(self.menu_items) - 1

    def accept_selection(self):
        selection = self.menu_items[self.selection_idx]
        selection[1](*selection[2])

    def enter_combat(self):
        base.blackboard['monsters'] = [
            self.player.monster.id
        ]
        base.change_state('Combat')

    def set_menu(self, new_menu):
        self.menu_items = self.menus[new_menu]
        self.selection_idx = 0
        self.update_ui({
            'menu_items': [i[0] for i in self.menu_items],
        })

    def train_stat(self, stat):
        stat_growth = 0

        attr = '{}_affinity'.format(stat)
        affinity = getattr(self.player.monster.breed, attr)
        success_chance = 60 + 10 * affinity
        great_chance = 5 + min(100 - success_chance, 0)

        if random.randrange(0, 99) < great_chance:
            stat_growth = 20

        if random.randrange(0, 99) < success_chance:
            stat_growth = 10

        attr = '{}_offset'.format(stat)
        old_stat = getattr(self.player.monster, attr)
        setattr(self.player.monster, attr, old_stat + stat_growth)

        print('{} grew by {}'.format(stat, stat_growth))
        print(self.player.monster)
