import random

from direct.actor.Actor import Actor
from direct.showbase.MessengerGlobal import messenger
import panda3d.core as p3d

from .. import gamedb
from .. import datamodels

from .gamestate import GameState
from .menuhelper import MenuHelper


_BG_VERT = """
#version 130

out vec2 texcoord;

const vec4 positions[4] = vec4[4](
    vec4(-1, -1, 0, 1),
    vec4( 1, -1, 0, 1),
    vec4(-1,  1, 0, 1),
    vec4( 1,  1, 0, 1)
);

const vec2 texcoords[4] = vec2[4](
    vec2(0, 0),
    vec2(1, 0),
    vec2(0, 1),
    vec2(1, 1)
);

void main() {
    gl_Position = positions[gl_VertexID];
    texcoord = texcoords[gl_VertexID];
}
"""

_BG_FRAG = """
#version 130

uniform sampler2D tex;
in vec2 texcoord;

out vec4 color;

void main() {
    color = vec4(texture2D(tex, texcoord).rgb, 1.0);
}
"""


class RanchState(GameState):
    def __init__(self):
        super().__init__()

        gdb = gamedb.get_instance()
        self.player = base.blackboard['player']

        # Load and display the monster model
        self.monster_actor = None
        self.load_monster_model()

        # Setup lighting
        self.light = p3d.DirectionalLight('dlight')
        self.lightnp = self.root_node.attach_new_node(self.light)
        self.lightnp.set_pos(2, -4, 4)
        self.lightnp.look_at(0, 0, 0)
        self.root_node.set_light(self.lightnp)

        # Setup backgrounds
        self.background_textures = {
            'base': base.loader.load_texture('ranchbg.png'),
            'market': base.loader.load_texture('marketbg.png'),
        }
        for tex in self.background_textures.values():
            if tex.get_num_components() == 4:
                tex.set_format(p3d.Texture.F_srgb_alpha)
            else:
                tex.set_format(p3d.Texture.F_srgb)
        self.background_image = self.root_node.attach_new_node(p3d.CardMaker('bgimg').generate())
        self.background_image.set_shader(p3d.Shader.make(p3d.Shader.SL_GLSL, _BG_VERT, _BG_FRAG))
        self.background_image.set_depth_test(False)
        self.background_image.set_depth_write(False)
        self.set_background('base')

        # Setup Camera
        base.camera.set_pos(-3, -5, 5)
        base.camera.look_at(0, 0, 1)

        # UI
        def accept_cb():
            if self.message_modal:
                self.display_message('')
                return True
            elif self._show_stats:
                self._show_stats = False
                return True
            return False

        def reject_cb():
            menu_name = self.menu_helper.current_menu
            if menu_name is 'training':
                self.menu_helper.set_menu('base')
            elif menu_name in ('monsters_stash', 'monsters_market'):
                self.menu_helper.set_menu('monsters')
            elif self._show_stats:
                self._show_stats = False

        self.menu_helper = MenuHelper(self, accept_cb, reject_cb)
        self.menu_helper.menus = {
            'base': [
                ('Combat', self.enter_combat, []),
                ('Train', self.menu_helper.set_menu, ['training']),
                ('Monster Stats', self.show_stats, []),
                ('Stash Monster', self.stash_monster, []),
                ('Save Game', base.change_state, ['Save']),
                ('Load Game', base.change_state, ['Load']),
                ('Quit', self.menu_helper.set_menu, ['quit']),
            ],
            'training': [
                ('Back', self.menu_helper.set_menu, ['base']),
                ('Hit Points', self.train_stat, ['hp']),
                ('Physical Attack', self.train_stat, ['physical_attack']),
                ('Magical Attack', self.train_stat, ['magical_attack']),
                ('Accuracy', self.train_stat, ['accuracy']),
                ('Evasion', self.train_stat, ['evasion']),
                ('Defense', self.train_stat, ['defense']),
            ],
            'monsters': [
                ('From Stash', self.menu_helper.set_menu, ['monsters_stash']),
                ('From Market', self.menu_helper.set_menu, ['monsters_market']),
            ],
            'monsters_stash': [
                ('Back', self.menu_helper.set_menu, ['monsters']),
            ],
            'monsters_market': [
                ('Back', self.menu_helper.set_menu, ['monsters']),
            ] + [
                (breed.name, self.get_monster, [breed.id]) for breed in gdb['breeds'].values()
            ],
            'quit': [
                ('Exit to Title Menu', base.change_state, ['Title']),
                ('Exit Game', messenger.send, ['escape']),
            ],
        }
        self.menu_helper.menu_headings = {
            'base': 'Ranch',
            'training': 'Training',
            'monsters': '',
            'monsters_stash': 'Select a Monster',
            'monsters_market': 'Select a Breed',
            'quit': '',
        }
        self.monster_menus = [
            'monsters',
            'monsters_stash',
            'monsters_market',
        ]
        self.update_monster_stash_ui()

        self.message = ""
        self.message_modal = False

        self._show_stats = False

        self.load_ui('ranch')

        self.menu_helper.set_menu('base')

    def cleanup(self):
        super().cleanup()

        self.menu_helper.cleanup()

    def load_monster_model(self):
        if self.monster_actor:
            self.monster_actor.cleanup()
            self.monster_actor.remove_node()

        if self.player.monster:
            breed = self.player.monster.breed
            monster_model = base.loader.load_model('{}.bam'.format(breed.bam_file))
            self.monster_actor = Actor(monster_model.find('**/{}'.format(breed.root_node)))
            self.monster_actor.set_h(180)
            self.monster_actor.loop(breed.anim_map['idle'])
            self.monster_actor.reparent_to(self.root_node)
        else:
            self.monster_actor = None

    def set_background(self, bgname):
        self.background_image.set_shader_input('tex', self.background_textures[bgname])

    def update_monster_stash_ui(self):
        del self.menu_helper.menus['monsters_stash'][1:]
        self.menu_helper.menus['monsters_stash'].extend([
            (monster.name, self.retrieve_monster, [idx])
            for idx, monster in enumerate(self.player.monster_stash)
        ])

    def update(self, dt):
        super().update(dt)

        if (not self.menu_helper.lock and not self.player.monster and
                self.menu_helper.current_menu not in self.monster_menus):
            self.load_monster_model()
            self.menu_helper.set_menu('monsters')
            self.display_message('Select a breed')
            self.set_background('market')

        self.update_ui({
            'show_stats': self._show_stats,
        })
        self.menu_helper.update_ui()

    def display_message(self, msg, modal=False):
        self.message = msg
        self.message_modal = modal
        self.menu_helper.lock = modal
        self.update_ui({
            'message': self.message,
            'message_modal': self.message_modal,
        })

    def enter_combat(self):
        base.blackboard['monsters'] = [
            self.player.monster.id
        ]
        base.change_state('Combat')

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

        stat_display = stat.replace('_', ' ').title()
        if stat_display == 'Hp':
            stat_display = 'HP'
        self.display_message('{} grew by {}'.format(stat_display, stat_growth), modal=True)

    def show_stats(self):
        self._show_stats = True
        monsterdict = self.player.monster.to_dict()
        monsterdict['breed'] = self.player.monster.breed.name
        self.update_ui({
            'monster': monsterdict
        })

    def stash_monster(self):
        self.player.monster_stash.append(self.player.monster)
        self.player.monster = None
        self.update_monster_stash_ui()

        self.display_message('Monster Stashed!', modal=True)

    def retrieve_monster(self, stashidx):
        gdb = gamedb.get_instance()

        self.player.monster = self.player.monster_stash.pop(stashidx)
        self.update_monster_stash_ui()
        gdb['monsters']['player_monster'] = self.player.monster

        self.display_message('')
        self.menu_helper.set_menu('base')
        self.load_monster_model()

    def get_monster(self, breed):
        gdb = gamedb.get_instance()

        breed = gdb['breeds'][breed]
        monster = datamodels.Monster({
            'id': 'player_monster',
            'name': breed.name,
            'breed': breed.id,
            'hp_offset': 0,
            'ap_offset': 0,
            'physical_attack_offset': 0,
            'magical_attack_offset': 0,
            'accuracy_offset': 0,
            'evasion_offset': 0,
            'defense_offset': 0,
        })
        monster.link(gdb)

        self.player.monster = monster
        gdb['monsters']['player_monster'] = monster

        self.display_message('')
        self.menu_helper.set_menu('base')
        self.load_monster_model()
        self.set_background('base')
