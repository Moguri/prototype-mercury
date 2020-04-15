import itertools

from direct.showbase.MessengerGlobal import messenger
import panda3d.core as p3d

from .. import gamedb
from ..monster import Monster, MonsterActor
from ..commonlighting import CommonLighting
from .. import bgnode

from .gamestate import GameState


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
        self.background_image = bgnode.generate(self.root_node)

        # Setup Background Music
        self.play_bg_music('woodland_fantasy')

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
            self.set_background('base')
            menu_items = [
                ('Battle', self.set_input_state, ['COMBAT']),
                ('Select Monster', self.set_input_state, ['SELECT_MONSTER']),
                ('Monster Stats', self.set_input_state, ['STATS']),
                ('Change Job', self.set_input_state, ['JOBS']),
                ('Dismiss Monster', self.set_input_state, ['DISMISS']),
            ]
            if len(self.player.monsters) < self.player.max_monsters:
                menu_items.insert(1, ('Market', self.set_input_state, ['MARKET']))
            if base.allow_saves:
                menu_items.extend([
                    ('Save Game', base.change_state, ['Save']),
                    ('Load Game', base.change_state, ['Load']),
                ])
            menu_items.append(('Quit', self.set_input_state, ['QUIT']))
            self.menu_helper.set_menu('Ranch', menu_items)
        elif next_state == 'SELECT_MONSTER':
            self.display_message('Select a monster', modal=True)
            prev_selection = self.monster_selection

            def update_monster_selection(delta):
                self.monster_selection += delta
                if self.monster_selection < 0:
                    self.monster_selection = len(self.monster_actors) - 1
                elif self.monster_selection >= len(self.monster_actors):
                    self.monster_selection = 0
            self.accept('move-left', update_monster_selection, [-1])
            self.accept('move-right', update_monster_selection, [1])

            self.accept('accept', self.set_input_state, ['MAIN'])

            def reject_sel():
                self.monster_selection = prev_selection
                self.input_state = 'MAIN'
            self.accept('reject', reject_sel)
        elif next_state == 'MARKET':
            self.load_monster_models([])
            base.camera.set_x(0)
            def get_monster(breedid):
                breed = gdb['breeds'][breedid]
                self.player.monsters.append(
                    Monster.make_new('player.monster', breed_id=breed.id)
                )
                self.load_monster_models()
                self.monster_selection = len(self.monster_actors) - 1
                back_to_main()
            menu_items = [
                (breed.name, get_monster, [breed.id])
                for breed in gdb['breeds'].values()
                if self.player.can_use_breed(breed)
            ]
            def market_reject():
                if self.player.monsters:
                    self.load_monster_models()
                    back_to_main()
            if self.player.monsters:
                menu_items.insert(0, ('Back', market_reject, []))
            self.menu_helper.set_menu('Select a Breed', menu_items)

            def show_breed(_idx=None):
                selection = self.menu_helper.current_selection
                if selection[0] == 'Back':
                    return
                breed = gdb['breeds'][selection[2][0]]
                self.load_monster_models([breed])
            show_breed()
            self.menu_helper.selection_change_cb = show_breed
            self.menu_helper.reject_cb = market_reject
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
        elif next_state == 'JOBS':
            self.load_monster_models([self.current_monster.breed], [self.current_monster.job.id])
            base.camera.set_x(0)
            def change_job(jobid):
                gdb = gamedb.get_instance()
                job = gdb['jobs'][jobid]
                self.current_monster.job = job
                self.display_message('')
                self.load_monster_models()
                back_to_main()

            def job_reject():
                self.load_monster_models()
                back_to_main()

            def show_job(_idx):
                selection = self.menu_helper.current_selection
                if selection[0] == 'Back':
                    jobid = self.current_monster.job.id
                else:
                    jobid = selection[2][0]
                self.load_monster_models([self.current_monster.breed], [jobid])

            self.menu_helper.set_menu('Select a Job', [
                ('Back', job_reject, []),
            ] + [
                (job.name, change_job, [job.id])
                for job in gdb['jobs'].values()
                if self.current_monster.can_use_job(job)
            ])
            self.menu_helper.selection_change_cb = show_job
            self.menu_helper.reject_cb = job_reject
        elif next_state == 'COMBAT':
            def enter_combat(ctype):
                base.blackboard['combat_type'] = ctype
                base.change_state('Combat')
            self.menu_helper.set_menu('', [
                ('Back', self.set_input_state, ['MAIN']),
                ('Skirmish', enter_combat, ['skirmish']),
                ('Boss Fight', enter_combat, ['boss']),
            ])
        elif next_state == 'DISMISS':
            mon = self.player.monsters.pop(self.monster_selection)
            self.display_message(f'Dismissed {mon.name}', modal=True)

            def accept_dismiss():
                self.monster_selection -= 1
                if self.monster_selection < 0:
                    self.monster_selection = 0
                if self.current_monster:
                    self.load_monster_models()
                    self.input_state = 'MAIN'
                else:
                    self.input_state = 'MARKET'
            self.accept('accept', accept_dismiss)
        elif next_state == 'QUIT':
            self.menu_helper.set_menu('', [
                ('Back', self.set_input_state, ['MAIN']),
                ('Exit to Title Menu', base.change_state, ['Title']),
                ('Exit Game', messenger.send, ['escape']),
            ])
        else:
            raise RuntimeError(f'Unknown state {next_state}')

        self._input_state = next_state

    def update(self, dt):
        super().update(dt)

        if self.input_state not in ('MARKET', 'JOBS'):
            base.camera.set_x(self.monster_actors[self.monster_selection].get_x(self.root_node))

    def load_monster_models(self, breeds=None, jobs=None):
        for monact in self.monster_actors:
            monact.cleanup()
            monact.remove_node()
        self.monster_actors = []
        labels = []

        if breeds is None:
            breeds = [i.breed for i in self.player.monsters]
            jobs = [i.job.id for i in self.player.monsters]
            labels = [i.name for i in self.player.monsters]

        if jobs is None:
            jobs = [i.default_job for i in breeds]

        if not labels:
            labels = itertools.repeat('')

        stride = 2
        offset = 0
        for breed, jobid, labelstr in zip(breeds, jobs, labels):
            actor = MonsterActor(breed, self.monsters_root, jobid)
            actor.set_h(-135)
            actor.set_pos(self.monsters_root, p3d.LVector3(offset, 0, 0))
            self.monster_actors.append(actor)

            label = p3d.TextNode('monster label')
            label.set_align(p3d.TextNode.ACenter)
            label.set_text(labelstr)
            labelnp = actor.attach_new_node(label)
            labelnp.set_pos(0, 0, 2.3)
            labelnp.set_scale(0.2)
            labelnp.set_billboard_point_eye()
            labelnp.set_bin("fixed", 0)
            labelnp.set_depth_test(False)
            labelnp.set_depth_write(False)
            labelnp.set_shader_auto(True)

            offset += stride

        if self.monster_actors:
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
