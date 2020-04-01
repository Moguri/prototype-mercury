from direct.actor.Actor import Actor
from direct.showbase.MessengerGlobal import messenger
import panda3d.core as p3d

from .. import gamedb
from ..monster import Monster

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
        self.light.set_color((3, 3, 3, 1))
        self.lightnp = self.root_node.attach_new_node(self.light)
        self.lightnp.set_pos(-2, -4, 4)
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
        self.background_image.set_bin('background', 0)
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
            if menu_name in ('monsters_market',):
                self.menu_helper.set_menu('base')
            elif self._show_stats:
                self._show_stats = False

        self.menu_helper = MenuHelper(self, accept_cb, reject_cb)
        self.menu_helper.menus = {
            'base': [
                ('Combat', self.enter_combat, []),
                ('Monster Stats', self.show_stats, []),
                ('Change Job', self.menu_helper.set_menu, ['jobs']),
                ('Save Game', base.change_state, ['Save']),
                ('Load Game', base.change_state, ['Load']),
                ('Quit', self.menu_helper.set_menu, ['quit']),
            ],
            'monsters_market': [
                ('Back', self.menu_helper.set_menu, ['base']),
            ] + [
                (breed.name, self.get_monster, [breed.id]) for breed in gdb['breeds'].values()
            ],
            'jobs': [
                ('Back', self.menu_helper.set_menu, ['base']),
            ] + [
                (job.name, self.change_job, [job.id]) for job in gdb['jobs'].values()
            ],
            'quit': [
                ('Exit to Title Menu', base.change_state, ['Title']),
                ('Exit Game', messenger.send, ['escape']),
            ],
        }
        self.menu_helper.menu_headings = {
            'base': 'Ranch',
            'monsters_market': 'Select a Breed',
            'quit': '',
        }

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

        if self.player.monsters:
            breed = self.player.monsters[0].breed
            monster_model = base.loader.load_model('{}.bam'.format(breed.bam_file))
            self.monster_actor = Actor(monster_model.find('**/{}'.format(breed.root_node)))
            self.monster_actor.set_h(180)
            self.monster_actor.loop(breed.anim_map['idle'])
            self.monster_actor.reparent_to(self.root_node)
        else:
            self.monster_actor = None

    def set_background(self, bgname):
        self.background_image.set_shader_input('tex', self.background_textures[bgname])

    def update(self, dt):
        super().update(dt)

        if (not self.menu_helper.lock and not self.player.monsters and
                self.menu_helper.current_menu != 'monsters_market'):
            self.load_monster_model()
            self.menu_helper.set_menu('monsters_market')
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
            self.player.monsters[0].id
        ]
        base.change_state('Combat')

    def show_stats(self):
        self._show_stats = True
        monsterdict = self.player.monsters[0].to_dict()
        monsterdict['breed'] = self.player.monsters[0].breed.name
        monsterdict['job'] = self.player.monsters[0].job.name
        self.update_ui({
            'monster': monsterdict
        })

    def get_monster(self, breedid):
        gdb = gamedb.get_instance()
        breed = gdb['breeds'][breedid]
        self.player.monsters.append(
            Monster.make_new('player.monster', breed.name, breed.id)
        )
        self.display_message('')
        self.menu_helper.set_menu('base')
        self.load_monster_model()
        self.set_background('base')

    def change_job(self, jobid):
        gdb = gamedb.get_instance()
        job = gdb['jobs'][jobid]
        self.player.monsters[0].job = job
        self.display_message('')
        self.menu_helper.set_menu('base')
