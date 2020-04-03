import random

from direct.actor.Actor import Actor
from direct.showbase.MessengerGlobal import messenger
import panda3d.core as p3d

from .. import gamedb
from ..monster import Monster

from .gamestate import GameState
from .commonlighting import CommonLighting


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
uniform float exposure_inv;
in vec2 texcoord;

out vec4 color;

void main() {
    color = vec4(texture2D(tex, texcoord).rgb, 1.0) * exposure_inv;
}
"""

SHADOW_CATCH_V = """
#version 130

#define MAX_LIGHTS 8

uniform struct p3d_LightSourceParameters {
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[MAX_LIGHTS];

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;

in vec4 p3d_Vertex;

out vec4 v_shadow_pos[MAX_LIGHTS];

void main() {
    vec4 vert_pos4 = p3d_ModelViewMatrix * p3d_Vertex;
    for (int i = 0; i < p3d_LightSource.length(); ++i) {
        v_shadow_pos[i] = p3d_LightSource[i].shadowViewMatrix * vert_pos4;
    }
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
"""

SHADOW_CATCH_F = """
#version 130

#define MAX_LIGHTS 8

uniform struct p3d_LightSourceParameters {
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[MAX_LIGHTS];

in vec4 v_shadow_pos[MAX_LIGHTS];
out vec4 color;

void main() {
    color = vec4(1.0, 1.0, 1.0, 0.5);
    for (int i = 0; i < p3d_LightSource.length(); ++i) {
        float shadow = shadow2DProj(p3d_LightSource[i].shadowMap, v_shadow_pos[i]).r;
        color.rgb *= shadow;
    }
    if (color.r > 0.0) {
        discard;
    }
}
"""

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


class RanchState(GameState):
    def __init__(self):
        super().__init__()

        self.player = base.blackboard['player']
        self.monster_selection = 0

        # Setup lighting
        self.lights_root = self.root_node.attach_new_node('light root')
        self.lighting = CommonLighting(self.lights_root, calc_shadow_bounds=False)
        self.lights_root.set_h(45)

        # Load and display the monster model
        self.monster_actors = []
        self.monsters_root = self.root_node.attach_new_node('monsters')
        self.load_monster_models()

        # Setup plane to catch shadows
        if p3d.ConfigVariableBool('enable-shadows').get_value():
            shadow_catcher = p3d.CardMaker('shadow_catcher').generate()
            shadow_catcher = self.root_node.attach_new_node(shadow_catcher)
            shadow_catcher.set_p(-90)
            shadow_catcher.set_scale(30)
            shadow_catcher.set_pos(-15, -15, 0)
            shadow_catcher.flatten_strong()
            shadow_catcher.set_transparency(p3d.TransparencyAttrib.M_alpha)
            shadow_catcher.set_shader(p3d.Shader.make(
                p3d.Shader.SL_GLSL,
                SHADOW_CATCH_V,
                SHADOW_CATCH_F
            ))

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
        self.background_image.set_shader_input('exposure_inv', 1.0 / base.render_pipeline.exposure)
        self.background_image.set_bin('background', 0)
        self.background_image.set_depth_test(False)
        self.background_image.set_depth_write(False)

        # Setup Camera
        base.camera.set_pos(0, -5, 5)
        base.camera.look_at(0, 0, 1)

        # UI
        self.message = ""
        self.message_modal = False

        self.load_ui('ranch')

        # Set initial input state
        if self.player.monsters:
            self.input_state = 'MAIN'
        else:
            self.input_state = 'MARKET'

    def set_input_state(self, next_state):
        self.display_message('')
        super().set_input_state(next_state)
        gdb = gamedb.get_instance()
        self.update_ui({
            'show_stats': False,
        })

        def back_to_main():
            self.input_state = 'MAIN'
        self.menu_helper.reject_cb = back_to_main

        if next_state == 'MAIN':
            self.menu_helper.set_menu('Ranch', [
                ('Combat', self.set_input_state, ['COMBAT']),
                ('Monster Stats', self.set_input_state, ['STATS']),
                ('Train', self.set_input_state, ['TRAIN']),
                ('Change Job', self.set_input_state, ['JOBS']),
                ('Save Game', base.change_state, ['Save']),
                ('Load Game', base.change_state, ['Load']),
                ('Quit', self.set_input_state, ['QUIT']),
            ])
            self.set_background('base')
        elif next_state == 'MARKET':
            def get_monster(breedid):
                breed = gdb['breeds'][breedid]
                monster_name = random.choice(RANDOM_NAMES)
                self.player.monsters.append(
                    Monster.make_new('player.monster', monster_name, breed.id)
                )
                self.load_monster_models()
                back_to_main()
            menu_items = [
                (breed.name, get_monster, [breed.id])
                for breed in gdb['breeds'].values()
                if self.player.can_use_breed(breed)
            ]
            if self.player.monsters:
                menu_items.insert(0, ('Back', back_to_main, []))
            self.menu_helper.set_menu('Select a Breed', menu_items)

            def show_breed(_idx=None):
                selection = self.menu_helper.current_selection
                if selection[0] == 'Back':
                    return
                breed = gdb['breeds'][selection[2][0]]
                self.load_monster_models([breed])
            show_breed()
            self.menu_helper.selection_change_cb = show_breed
            self.display_message('Select a breed')
            self.set_background('market')
        elif next_state == 'STATS':
            self.update_ui({
                'show_stats': True,
            })
            monsterdict = self.current_monster.to_dict()
            monsterdict['breed'] = self.current_monster.breed.name
            monsterdict['job'] = self.current_monster.job.name
            self.update_ui({
                'monster': monsterdict
            })
            self.accept('accept', back_to_main)
        elif next_state == 'TRAIN':
            monster = self.current_monster
            job = monster.job
            monster.job_levels[job.id] += 1
            self.display_message(
                f'{job.name} raised to level  {monster.job_levels[job.id]}',
                modal=True
            )
            self.accept('accept', back_to_main)

        elif next_state == 'JOBS':
            def change_job(jobid):
                gdb = gamedb.get_instance()
                job = gdb['jobs'][jobid]
                self.current_monster.job = job
                self.display_message('')
                back_to_main()

            self.menu_helper.set_menu('Select a Job', [
                ('Back', back_to_main, []),
            ] + [
                (job.name, change_job, [job.id])
                for job in gdb['jobs'].values()
                if self.current_monster.job.id != job.id and self.current_monster.can_use_job(job)
            ])
        elif next_state == 'COMBAT':
            base.blackboard['monsters'] = [
                self.current_monster.id
            ]
            base.change_state('Combat')
        elif next_state == 'QUIT':
            self.menu_helper.set_menu('', [
                ('Back', self.set_input_state, ['MAIN']),
                ('Exit to Title Menu', base.change_state, ['Title']),
                ('Exit Game', messenger.send, ['escape']),
            ])
        else:
            raise RuntimeError(f'Unknown state {next_state}')

        self._input_state = next_state

    def load_monster_models(self, breeds=None):
        for monact in self.monster_actors:
            monact.cleanup()
            monact.remove_node()
        self.monster_actors = []

        if breeds is None:
            breeds = [i.breed for i in self.player.monsters]


        stride = 2
        offset = 0
        for breed in breeds:
            model = base.loader.load_model('{}.bam'.format(breed.bam_file))
            actor = Actor(model.find('**/{}'.format(breed.root_node)))
            actor.set_h(-135)
            actor.set_pos(self.monsters_root, p3d.LVector3(offset, 0, 0))
            actor.loop(breed.anim_map['idle'])
            actor.reparent_to(self.monsters_root)
            offset += stride
            self.monster_actors.append(actor)
        self.lighting.recalc_bounds(self.monsters_root)

    def set_background(self, bgname):
        self.background_image.set_shader_input('tex', self.background_textures[bgname])

    def display_message(self, msg, modal=False):
        self.message = msg
        self.message_modal = modal
        self.menu_helper.lock = modal
        self.update_ui({
            'message': self.message,
            'message_modal': self.message_modal,
        })

    @property
    def current_monster(self):
        if not self.player.monsters:
            return None
        return self.player.monsters[self.monster_selection]
