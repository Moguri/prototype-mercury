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


class WorkshopState(GameState):
    def __init__(self):
        super().__init__()

        gdb = gamedb.get_instance()

        self.player = base.blackboard['player']
        self.monster_selection = 0

        self.monster_actors = []
        self.monsters_root = self.root_node.attach_new_node('monsters')

        # Setup lighting
        self.lights_root = self.root_node.attach_new_node('light root')
        self.lighting = CommonLighting(self.lights_root, calc_shadow_bounds=False)
        self.lights_root.set_h(45)

        # Pre-load all monster models
        forms = []
        jobs = []
        for form in gdb['forms'].values():
            for skin in form.skins:
                forms.append(form)
                jobs.append(skin)
        self.load_monster_models(forms, jobs)

        # Load and display the player monster models
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
            'base': (
                base.loader.load_texture('backgrounds/ranchbg.png'),
                base.loader.load_texture('backgrounds/ranchfg.png'),
            ),
            'foundry': (
                base.loader.load_texture('backgrounds/marketbg.png'),
                base.loader.load_texture('backgrounds/marketfg.png'),
            ),
        }
        for tex in (i for texs in self.background_textures.values() for i in texs):
            if tex.get_num_components() == 4:
                tex.set_format(p3d.Texture.F_srgb_alpha)
            else:
                tex.set_format(p3d.Texture.F_srgb)
        self.background_image = bgnode.generate(self.root_node)
        self.foreground_image = bgnode.generate(self.root_node, foreground=True)
        self.foreground_image.set_transparency(p3d.TransparencyAttrib.M_alpha)

        # Setup Background Music
        self.play_bg_music('woodland_fantasy')

        # Setup Camera
        base.camera.set_pos(0, -5, 6)
        base.camera.look_at(0, 0, 1)

        # UI
        self.message = ""
        self.message_modal = False

        self.load_ui('workshop')

        # Set initial input state
        if self.player.monsters:
            self.input_state = 'MAIN'
        else:
            self.input_state = 'FOUNDRY'

    def enter_state(self):
        super().enter_state()

        self.display_message('')
        self.update_ui({
            'show_stats': False,
        })

        def back_to_main():
            self.input_state = 'MAIN'
        self.menu_helper.reject_cb = back_to_main

    def enter_main(self):
        self.set_background('base')
        menu_items = [
            ('Battle', self.set_input_state, ['COMBAT']),
            ('Select Golem', self.set_input_state, ['SELECT_MONSTER']),
            ('Golem Stats', self.set_input_state, ['STATS']),
            ('Change Job', self.set_input_state, ['JOBS']),
            ('Abilities', self.set_input_state, ['ABILITIES']),
            ('Dismiss Golem', self.set_input_state, ['DISMISS']),
            ('Quit', self.set_input_state, ['QUIT']),
        ]
        if len(self.player.monsters) < self.player.max_monsters:
            menu_items.insert(1, ('Foundry', self.set_input_state, ['FOUNDRY']))
        self.menu_helper.set_menu('Workshop', menu_items)

    def enter_select_monster(self):
        self.display_message('Select a golem', modal=True)
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

    def enter_foundry(self):
        gdb = gamedb.get_instance()
        self.load_monster_models([])
        base.camera.set_x(0)
        def get_monster(formid):
            form = gdb['forms'][formid]
            self.player.monsters.append(
                Monster.make_new('player.monster', form_id=form.id)
            )
            self.load_monster_models()
            self.monster_selection = len(self.monster_actors) - 1
            self.input_state = 'MAIN'
        menu_items = [
            (form.name, get_monster, [form.id])
            for form in gdb['forms'].values()
            if self.player.can_use_form(form)
        ]
        def foundry_reject():
            if self.player.monsters:
                self.load_monster_models()
                self.input_state = 'MAIN'
        if self.player.monsters:
            menu_items.insert(0, ('Back', foundry_reject, []))
        self.menu_helper.set_menu('Select a Form', menu_items)

        def show_form(_idx=None):
            selection = self.menu_helper.current_selection
            if selection[0] == 'Back':
                return
            form = gdb['forms'][selection[2][0]]
            self.load_monster_models([form])
        show_form()
        self.menu_helper.selection_change_cb = show_form
        self.menu_helper.reject_cb = foundry_reject
        self.display_message('Select a form')
        self.set_background('foundry')

    def enter_stats(self):
        self.update_ui({
            'show_stats': True,
        })
        monsterdict = self.current_monster.to_dict()
        monsterdict['form'] = self.current_monster.form.name
        monsterdict['job'] = self.current_monster.job.name
        self.update_ui({
            'monster': monsterdict
        })
        self.accept('accept', self.set_input_state, ['MAIN'])

    def enter_jobs(self):
        gdb = gamedb.get_instance()
        self.load_monster_models([self.current_monster.form], [self.current_monster.job.id])
        base.camera.set_x(0)
        def change_job(jobid):
            job = gdb['jobs'][jobid]
            self.current_monster.job = job
            self.display_message('')
            self.load_monster_models()
            self.input_state = 'MAIN'

        def job_reject():
            self.load_monster_models()
            self.input_state = 'MAIN'

        def show_job(_idx):
            selection = self.menu_helper.current_selection
            if selection[0] == 'Back':
                jobid = self.current_monster.job.id
            else:
                jobid = selection[2][0]
            self.load_monster_models([self.current_monster.form], [jobid])

        self.menu_helper.set_menu('Select a Job', [
            ('Back', job_reject, []),
        ] + [
            (
                f'{job.name} (lvl {self.current_monster.job_level(job)})' + \
                    ('*' if job.id == self.current_monster.job.id else ''),
                change_job,
                [job.id]
            )
            for job in self.current_monster.available_jobs
        ])
        self.menu_helper.selection_change_cb = show_job
        self.menu_helper.reject_cb = job_reject

    def enter_abilities(self, menu_idx=0):
        gdb = gamedb.get_instance()
        unspentjp = self.current_monster.jp_unspent.get(self.current_monster.job.id, 0)
        learnedids = [ability.id for ability in self.current_monster.abilities]

        def curr_ranks(stat):
            jobid = self.current_monster.job.id
            upgrades = self.current_monster.stat_upgrades.get(jobid, {})
            return upgrades.get(stat, 0)

        def learn_ability(ability):
            if unspentjp >= ability.jp_cost and ability.id not in learnedids:
                self.current_monster.add_ability(ability)
                self.set_input_state('ABILITIES', menu_idx=self.menu_helper.selection_idx)

        def upgrade_stat(stat, max_rank):
            if unspentjp >= 100 and curr_ranks(stat) < max_rank:
                self.current_monster.upgrade_stat(stat)
                self.set_input_state('ABILITIES', menu_idx=self.menu_helper.selection_idx)

        pretty_stat_names = {
            'hp': 'HP',
            'ep': 'EP',
            'physical_attack': 'PA',
            'magical_attack': 'MA',
            'movement': 'Movement',
        }

        def build_menu():
            self.menu_helper.set_menu(f'Available JP: {unspentjp}', [
                ('Back', self.set_input_state, ['MAIN']),
            ] + [
                (
                    f'Upgrade {pretty_stat_names[stat]} {curr_ranks(stat)}/{max_rank} (100 JP)' + \
                        ('*' if curr_ranks(stat) == max_rank else ''),
                    upgrade_stat,
                    [stat, max_rank]
                )
                for stat, max_rank in self.current_monster.job.stat_upgrades.items()
            ] + [
                (
                    f'{ability.name} ({ability.jp_cost} JP)' + \
                        ('*' if ability.id in learnedids else ''),
                    learn_ability,
                    [ability]
                )
                for ability in [gdb['abilities'][i] for i in self.current_monster.job.abilities]
            ])
            self.menu_helper.move_to_index(menu_idx, play_sfx=False)
        build_menu()

    def enter_combat(self):
        def enter_combat(ctype):
            base.blackboard['combat_type'] = ctype
            base.change_state('Combat')
        self.menu_helper.set_menu('', [
            ('Back', self.set_input_state, ['MAIN']),
            ('Skirmish', enter_combat, ['skirmish']),
            ('Boss Fight', enter_combat, ['boss']),
        ])

    def enter_dismiss(self):
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
                self.input_state = 'FOUNDRY'
        self.accept('accept', accept_dismiss)

    def enter_quit(self):
        self.menu_helper.set_menu('', [
            ('Back', self.set_input_state, ['MAIN']),
            ('Exit to Title Menu', base.change_state, ['Title']),
            ('Exit Game', messenger.send, ['quit']),
        ])

    def update(self, dt):
        super().update(dt)

        if self.input_state not in ('FOUNDRY', 'JOBS'):
            base.camera.set_x(self.monster_actors[self.monster_selection].get_x(self.root_node))

    def load_monster_models(self, forms=None, jobs=None):
        for monact in self.monster_actors:
            monact.cleanup()
            monact.remove_node()
        self.monster_actors = []
        labels = []

        if forms is None:
            forms = [i.form for i in self.player.monsters]
            jobs = [i.job.id for i in self.player.monsters]
            labels = [i.name for i in self.player.monsters]

        if jobs is None:
            jobs = [i.default_job for i in forms]

        if not labels:
            labels = itertools.repeat('')

        stride = 2
        offset = 0
        for form, jobid, labelstr in zip(forms, jobs, labels):
            actor = MonsterActor(form, self.monsters_root, jobid)
            actor.set_h(45)
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
            labelnp.set_color_scale((0, 0, 0, 1))
            labelnp.set_light_off()

            offset += stride

        if self.monster_actors:
            self.lighting.recalc_bounds(self.monsters_root)

    def set_background(self, bgname):
        self.background_image.set_shader_input('tex', self.background_textures[bgname][0])
        self.foreground_image.set_shader_input('tex', self.background_textures[bgname][1])

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
