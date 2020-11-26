import itertools

from direct.showbase.MessengerGlobal import messenger
from direct.interval import IntervalGlobal as intervals
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
        forms = gdb['forms'].values()
        self.load_monster_models(forms)

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

        self.display_message(None)
        self.update_ui({
            'show_stats': False,
            'num_golems': len(self.player.monsters),
            'max_golems': self.player.max_monsters
        })

        def back_to_main():
            self.input_state = 'MAIN'
        self.menu_helper.reject_cb = back_to_main

    def enter_main(self):
        self.set_background('base')
        menu_items = [
            ('Battle', self.set_input_state, ['COMBAT']),
            ('Golem Stats', self.set_input_state, ['STATS']),
            ('Dismiss Golem', self.set_input_state, ['DISMISS']),
            ('Quit', self.set_input_state, ['QUIT']),
        ]
        if len(self.player.monsters) < self.player.max_monsters:
            menu_items.insert(1, ('Foundry', self.set_input_state, ['FOUNDRY']))
        self.menu_helper.set_menu('Workshop', menu_items)

        def update_monster_selection(delta):
            self.monster_selection += delta
            if self.monster_selection < 0:
                self.monster_selection = len(self.monster_actors) - 1
            elif self.monster_selection >= len(self.monster_actors):
                self.monster_selection = 0
            self.set_camera_x(
                self.monster_actors[self.monster_selection].get_x(self.root_node)
            )
        update_monster_selection(0)
        self.accept('move-left', update_monster_selection, [-1])
        self.accept('move-right', update_monster_selection, [1])

    def enter_foundry(self):
        gdb = gamedb.get_instance()
        self.load_monster_models([])
        self.set_camera_x(0)
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

        def show_form(selection):
            if selection[0] == 'Back':
                return
            form = gdb['forms'][selection[2][0]]
            self.load_monster_models([form])
            self.display_message(form.description)
        show_form(self.menu_helper.current_selection)
        self.menu_helper.selection_change_cb = show_form
        self.menu_helper.reject_cb = foundry_reject
        self.display_message('Select a form')
        self.set_background('foundry')

    def enter_stats(self):
        self.set_background('base')

        self.set_camera_x(base.get_aspect_ratio() * 1.25)
        def update_monster_selection(delta):
            self.monster_selection += delta
            if self.monster_selection < 0:
                self.monster_selection = len(self.player.monsters) - 1
            elif self.monster_selection >= len(self.player.monsters):
                self.monster_selection = 0
            self.load_monster_models(
                [self.current_monster.form],
                [self.current_monster.weapon.id]
            )
            self.update_ui({
                'monster': self.current_monster.to_dict()
            })
        update_monster_selection(0)
        self.accept('move-left', update_monster_selection, [-1])
        self.accept('move-right', update_monster_selection, [1])

        self.update_ui({
            'show_stats': True,
        })

        def add_power():
            if self.current_monster.power_available < self.current_monster.MAX_POWER:
                self.current_monster.power_available += 1
            else:
                self.menu_helper.sfx_reject.play()
            self.update_ui({
                'monster': self.current_monster.to_dict()
            })

        def toggle_ability(ability, learned_list):
            if ability.id in learned_list:
                learned_list.remove(ability.id)
            elif self.current_monster.power_spent < self.current_monster.power_available:
                learned_list.append(ability.id)
            else:
                self.menu_helper.sfx_reject.play()

            self.update_ui({
                'monster': self.current_monster.to_dict()
            })
            prev_idx = self.menu_helper.selection_idx
            self.menu_helper.set_menu('', build_menu())
            self.menu_helper.move_to_index(prev_idx, play_sfx=False)

        def change_weapon():
            self.set_input_state('WEAPON')

        def gen_ability_menu(abilities, learned):
            items = []

            for ability in abilities:
                is_learned = ability.id in learned
                aname = ability.name
                if is_learned:
                    aname += '*'
                items.append((aname, toggle_ability, (ability, learned)))
            return items

        def build_menu():
            return [
                ('Add', add_power, []),
                *gen_ability_menu(
                    self.current_monster.form.abilities,
                    self.current_monster.abilities_learned_form
                ),
                (self.current_monster.weapon.name, change_weapon, []),
                *gen_ability_menu(
                    self.current_monster.weapon.abilities,
                    self.current_monster.abilities_learned_weapon
                ),
            ]

        self.update_ui({
            'num_form_abilities': len(self.current_monster.form.abilities),
            'num_weapon_abilities': len(self.current_monster.weapon.abilities),
        })

        def select(item):
            item_func_name = item[1].__name__
            if item_func_name == 'add_power':
                self.display_message(
                    'Add more power to this golem'
                )
            elif item_func_name == 'change_weapon':
                self.display_message(
                    'Select a different weapon for this golem'
                )
            else:
                ability = item[2][0]
                self.display_message(ability.description)
        self.menu_helper.selection_change_cb = select
        self.menu_helper.set_menu('', build_menu())
        select(self.menu_helper.current_selection)

    def exit_stats(self):
        self.load_monster_models()

    def enter_weapon(self):
        gdb = gamedb.get_instance()
        self.load_monster_models([self.current_monster.form], [self.current_monster.weapon.id])
        self.set_camera_x(0)
        def change_weapon(wepid):
            self.current_monster.weapon = wepid
            self.input_state = 'STATS'

        def reject():
            self.input_state = 'STATS'

        def select(selection):
            if selection[0] == 'Back':
                wepid = self.current_monster.weapon.id
            else:
                wepid = selection[2][0]
            self.load_monster_models([self.current_monster.form], [wepid])

        self.menu_helper.set_menu('Select a Weapon', [
            ('Back', reject, []),
        ] + [
            (
                f'{weapon.name}' + \
                    ('*' if weapon.id == self.current_monster.weapon.id else ''),
                change_weapon,
                [weapon.id]
            )
            for weapon in sorted(gdb['weapons'].values(), key=lambda x: x.name)
            if self.current_monster.can_use_weapon(weapon, self.player.tags)
        ])
        self.menu_helper.selection_change_cb = select
        self.menu_helper.reject_cb = reject

    def exit_weapon(self):
        self.load_monster_models()

    def enter_combat(self):
        def enter_combat(ctype):
            base.blackboard['combat_type'] = ctype
            base.change_state('Combat')
        menu_items = [
            ('Back', self.set_input_state, ['MAIN']),
            ('Skirmish', enter_combat, ['skirmish']),
        ]
        if self.player.rank < self.player.MAX_RANK:
            menu_items.append(('Tournament', enter_combat, ['tournament']))
        self.menu_helper.set_menu('', menu_items)

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

    def load_monster_models(self, forms=None, weapons=None):
        for monact in self.monster_actors:
            monact.cleanup()
            monact.remove_node()
        self.monster_actors = []
        labels = []

        if forms is None:
            forms = [i.form for i in self.player.monsters]
            labels = [i.name for i in self.player.monsters]
            weapons = [i.weapon for i in self.player.monsters]

        if not labels:
            labels = itertools.repeat('')

        if weapons is None:
            weapons = itertools.repeat(None)

        stride = 2
        offset = 0
        for form, weapon, labelstr in zip(forms, weapons, labels):
            actor = MonsterActor(form, self.monsters_root, weapon)
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

    def set_camera_x(self, newx):
        campos = base.camera.get_pos()
        campos.x = newx
        intervals.LerpPosInterval(
            base.camera,
            0.1,
            campos,
            blendType='easeInOut'
        ).start()

    def display_message(self, msg, modal=False):
        self.message = msg
        self.message_modal = modal
        if modal:
            self.menu_helper.lock = True
        self.update_ui({
            'message': self.message,
            'message_modal': self.message_modal,
        })

    @property
    def current_monster(self):
        if not self.player.monsters:
            return None
        return self.player.monsters[self.monster_selection]
