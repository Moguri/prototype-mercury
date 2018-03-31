import json
import math
import os
import sys

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
import panda3d.core as p3d

import cefpanda
import blenderpanda

p3d.load_prc_file_data(
    '',
    'win-size 1280 720\n'
    'framebuffer-multisample 1\n'
    'multisamples 8\n'
)


if hasattr(sys, 'frozen'):
    APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    APP_ROOT_DIR = os.path.dirname(__file__)
if not APP_ROOT_DIR:
    print('empty app_root_dir')
    sys.exit()


class CameraController():
    def __init__(self, camera, combatants):
        self.camera = camera
        self.combatants = combatants
        self.widget = camera.get_parent().attach_new_node('camera_widget')

        self.camera.reparent_to(self.widget)
        self.widget.set_p(-20.0)
        self.widget.set_z(1.0)
        self.camera.set_pos(self.widget, p3d.LVecBase3(0.0, -7.5, 0.0))

    def update(self, _):
        positions = [combatant.path.get_x() for combatant in self.combatants]

        target_pos = math.fsum(positions) / len(positions)
        current_pos = self.widget.get_x()
        movement = 0.035 * (target_pos - current_pos)
        new_pos = current_pos + movement
        self.widget.set_x(new_pos)

        distance = max(positions) - min(positions)
        offset_factor = (distance - 2.0) / 8.0
        target_offset = offset_factor * 10.0 + 7.5
        current_offset = -self.camera.get_y(self.widget)
        offset_delta = 0.01 * (target_offset - current_offset)
        offset_vector = p3d.LVecBase3(0.0, -(current_offset + offset_delta), 0.0)
        self.camera.set_pos(self.widget, offset_vector)

        return Task.cont


class Ability:
    def __init__(self):
        self.name = 'Ability'
        self.cost = 10

        self.range = [0]

        self.effects = [
            {
                'type': 'damage',
                'parameters': {
                    'physical_coef': 1.0,
                    'magical_coef': 0.0,
                    'base_coef': 0.0,
                }
            }
        ]


class Combatant:
    def __init__(self, scene_path, ability_inputs):
        self.path = base.loader.load_model('monster.bam')
        self.path.reparent_to(scene_path)

        self.name = 'CatShark'

        self.max_hp = 100
        self.current_hp = 100

        self.max_ap = 100
        self.current_ap = 0

        self.ap_per_second = 5

        self.ability_inputs = ability_inputs
        self.abilities = [Ability() for i in range(4)]

        self.range_index = 0

    def update(self, dt, range_index):
        self.range_index = range_index
        self.current_ap += self.ap_per_second * dt
        self.current_ap = min(self.current_ap, self.max_ap)

    def get_state(self):
        return {
            'name': self.name,
            'hp_current': self.current_hp,
            'hp_max': self.max_hp,
            'ap_current': int(self.current_ap),
            'ap_max': self.max_ap,
            'abilities': [{
                'name': ability.name,
                'input': _input.upper(),
                'range': ability.range,
                'cost': ability.cost,
                'usable': self._ability_is_usable(ability),
            } for ability, _input in zip(self.abilities, self.ability_inputs)],
        }

    def _ability_is_usable(self, ability):
        return ability.cost < self.current_ap and self.range_index in ability.range

    def use_ability(self, index):
        ability = self.abilities[index]
        if not self._ability_is_usable(ability):
            return

        self.current_ap -= ability.cost


class CombatState(DirectObject):
    def __init__(self, root_np):
        super().__init__()

        self.time_remaining = 60
        self.range_index = 0

        self.arena_model = base.loader.load_model('arena.bam')
        self.arena_model.reparent_to(root_np)

        self.combatants = [
            Combatant(self.arena_model, ['a', 's', 'd', 'f']),
            Combatant(self.arena_model, ['q', 'w', 'e', 'r']),
        ]
        self.combatants[0].path.set_x(-1.0)
        self.combatants[1].path.set_x(1.0)

        # Combatant 0 inputs
        for idx, inp in enumerate(self.combatants[0].ability_inputs):
            self.accept(inp, self.combatants[0].use_ability, [idx])
        self.accept('j', self.move_combatant, [0, -2.0])
        self.accept('k', self.move_combatant, [0, 2.0])

        # Combatant 1 inputs
        for idx, inp in enumerate(self.combatants[1].ability_inputs):
            self.accept(inp, self.combatants[1].use_ability, [idx])
        self.accept('u', self.move_combatant, [1, -2.0])
        self.accept('i', self.move_combatant, [1, 2.0])

        # UI
        self.ui = cefpanda.CEFPanda()
        self.load_ui('main')

        self.update_ui({'timer': 45})

        base.taskMgr.add(self.update_state, 'Combat State')

    def load_ui(self, uiname):
        self.ui.load(os.path.join(APP_ROOT_DIR, 'ui', '{}.html'.format(uiname)))

    def update_ui(self, new_state):
        data = json.dumps(new_state)
        self.ui.execute_js('update_state({})'.format(data), onload=True)

    def move_combatant(self, index, delta):
        new_positions = [combatant.path.get_x() for combatant in self.combatants]

        new_position = new_positions[index] + delta
        if abs(new_position) > 10:
            return

        new_positions[index] = new_position

        distance = max(new_positions) - min(new_positions)

        if distance > 8 or distance < 2:
            return

        self.range_index = int((distance - 2) // 2)
        combatant = self.combatants[index]
        combatant.path.set_x(combatant.path.get_x() + delta)

    def update_state(self, task):
        dt = p3d.ClockObject.get_global_clock().get_dt()
        self.time_remaining = 60 - task.time

        for combatant in self.combatants:
            combatant.update(dt, self.range_index)

        state = {
            'timer': math.floor(self.time_remaining),
            'range': self.range_index,
            'player_monster': self.combatants[0].get_state(),
            'opponent_monster': self.combatants[1].get_state(),
        }

        self.update_ui(state)

        return Task.cont


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        self.accept('escape', sys.exit)

        self.disable_mouse()
        self.render.set_shader_auto()
        self.render.set_antialias(p3d.AntialiasAttrib.MAuto)

        self.combat = CombatState(self.render)

        self.cam_controller = CameraController(self.camera, self.combat.combatants)
        self.taskMgr.add(self.cam_controller.update, 'Camera Controller')


APP = GameApp()
APP.run()
