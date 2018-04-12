import json
import math
import os
import sys

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.interval import IntervalGlobal as intervals
import panda3d.core as p3d

import cefpanda
import blenderpanda
import eventmapper
import effects
from combatant import Combatant
from gamedb import GameDB


if hasattr(sys, 'frozen'):
    APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    APP_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if not APP_ROOT_DIR:
    print('empty app_root_dir')
    sys.exit()

# Load config files before ShowBase is initialized
CONFIG_DIR = os.path.join(APP_ROOT_DIR, 'config')
p3d.load_prc_file(os.path.join(CONFIG_DIR, 'game.prc'))
p3d.load_prc_file(os.path.join(CONFIG_DIR, 'inputs.prc'))
p3d.load_prc_file(os.path.join(CONFIG_DIR, 'user.prc'))


class CameraController():
    def __init__(self, camera, combatants):
        self.camera = camera
        self.combatants = combatants
        self._old_cam_parent = camera.get_parent()
        self.widget = camera.get_parent().attach_new_node('camera_widget')

        self.camera.reparent_to(self.widget)
        self.widget.set_p(-20.0)
        self.widget.set_z(1.0)
        self.camera.set_pos(self.widget, p3d.LVecBase3(0.0, -7.5, 0.0))

    def cleanup(self):
        self.camera.reparent_to(self._old_cam_parent)
        self.widget.remove_node()

    def update(self):
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





class GameState(DirectObject):
    def __init__(self):
        super().__init__()
        self.root_node = p3d.NodePath('State Root')
        self.root_node.reparent_to(base.render)

    def cleanup(self):
        self.ignoreAll()
        self.root_node.remove_node()
        self.root_node = None

    def update(self, dt):
        pass


class CombatState(GameState):
    COMBAT_MAX_TIME = 60

    def __init__(self):
        super().__init__()

        self.lock_controls = 0
        self.range_index = 0

        self.arena_model = base.loader.load_model('arena.bam')
        self.arena_model.reparent_to(self.root_node)

        self.combatants = [
            Combatant(self.arena_model, ['p1-ability{}'.format(i) for i in range(4)]),
            Combatant(self.arena_model, ['p2-ability{}'.format(i) for i in range(4)]),
        ]
        self.combatants[0].path.set_x(-1.0)
        self.combatants[0].path.set_h(-90)
        self.combatants[0].target = self.combatants[1]
        self.combatants[1].path.set_x(1.0)
        self.combatants[1].path.set_h(90)
        self.combatants[1].target = self.combatants[0]

        # Combatant 0 inputs
        for idx, inp in enumerate(self.combatants[0].ability_inputs):
            self.accept(inp, self.use_ability, [self.combatants[0], idx])
        self.accept('p1-move-left', self.move_combatant, [0, -2.0])
        self.accept('p1-move-right', self.move_combatant, [0, 2.0])

        # Combatant 1 inputs
        for idx, inp in enumerate(self.combatants[1].ability_inputs):
            self.accept(inp, self.use_ability, [self.combatants[1], idx])
        self.accept('p2-move-left', self.move_combatant, [1, -2.0])
        self.accept('p2-move-right', self.move_combatant, [1, 2.0])

        def restart_state():
            base.change_state(CombatState)
        self.accept('space', restart_state)

        self.combat_timer = p3d.ClockObject()

        # UI
        base.load_ui('main')

        self.cam_controller = CameraController(base.camera, self.combatants)

    def cleanup(self):
        super().cleanup()
        self.cam_controller.cleanup()
        self.cam_controller = None

        base.taskMgr.remove('Combat State')

    def move_combatant(self, index, delta):
        if self.lock_controls:
            return

        new_positions = [combatant.path.get_x() for combatant in self.combatants]

        new_position = new_positions[index] + delta
        if abs(new_position) > 10:
            return

        new_positions[index] = new_position

        distance = max(new_positions) - min(new_positions)

        if distance > 8 or distance < 2:
            return

        combatant = self.combatants[index]
        if combatant.current_ap < combatant.move_cost:
            return

        combatant.current_ap -= combatant.move_cost
        combatant.path.set_x(combatant.path.get_x() + delta)
        self.range_index = int((distance - 2) // 2)

    def use_ability(self, combatant, index):
        if self.lock_controls:
            return

        ability = combatant.abilities[index]
        if not combatant.ability_is_usable(ability):
            return

        combatant.current_ap -= ability.cost

        sequence = effects.sequence_from_effects(combatant, ability.effects)

        def cleanup():
            self.lock_controls = 0
            combatant.path.loop('cg.Run')
        sequence.append(intervals.Func(cleanup))
        self.lock_controls = 1
        sequence.start()

    def update(self, dt):
        self.cam_controller.update()

        combat_time = self.combat_timer.get_real_time()
        time_remaining = self.COMBAT_MAX_TIME - combat_time
        if time_remaining < 0:
            base.change_state(CombatState)
            return

        for combatant in self.combatants:
            combatant.update(dt, self.range_index)

        state = {
            'timer': math.floor(time_remaining),
            'range': self.range_index,
            'player_monster': self.combatants[0].get_state(),
            'opponent_monster': self.combatants[1].get_state(),
        }

        base.ui.execute_js('update_state({})'.format(json.dumps(state)), onload=True)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        GameDB.get_instance()

        self.win.set_close_request_event('escape')
        self.accept('escape', sys.exit)

        self.disable_mouse()
        self.render.set_shader_auto()
        self.render.set_antialias(p3d.AntialiasAttrib.MAuto)

        self.event_mapper = eventmapper.EventMapper()

        # UI
        self.ui = cefpanda.CEFPanda()

        # Game states
        self.current_state = CombatState()
        def update_gamestate(task):
            self.current_state.update(p3d.ClockObject.get_global_clock().get_dt())
            return task.cont
        self.taskMgr.add(update_gamestate, 'GameState')

    def change_state(self, next_state):
        self.current_state.cleanup()
        self.current_state = next_state()

    def load_ui(self, uiname):
        self.ui.load(os.path.join(APP_ROOT_DIR, 'ui', '{}.html'.format(uiname)))



APP = GameApp()
APP.run()
