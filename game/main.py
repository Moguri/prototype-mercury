import math
import os
import sys

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
import panda3d.core as p3d

import cefpanda
import blenderpanda

p3d.load_prc_file_data(
    '',
    'win-size 1280 720'
)


if hasattr(sys, 'frozen'):
    APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    APP_ROOT_DIR = os.path.dirname(__file__)
if not APP_ROOT_DIR:
    print("empty app_root_dir")
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
        positions = [model.get_x() for model in self.combatants]

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


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        self.accept('escape', sys.exit)

        self.arena_model = self.loader.load_model('arena.bam')
        self.arena_model.reparent_to(self.render)

        self.monster_a_model = self.loader.load_model('monster.bam')
        self.monster_a_model.reparent_to(self.arena_model)
        self.monster_a_model.set_pos(-1.0, 0.0, 0.0)

        self.monster_b_model = self.loader.load_model('monster.bam')
        self.monster_b_model.reparent_to(self.arena_model)
        self.monster_b_model.set_pos(1.0, 0.0, 0.0)

        self.accept('j', self.move_combatant, [0, -2.0])
        self.accept('k', self.move_combatant, [0, 2.0])
        self.accept('u', self.move_combatant, [1, -2.0])
        self.accept('i', self.move_combatant, [1, 2.0])

        self.disable_mouse()
        self.render.set_shader_auto()

        self.combatants = [
            self.monster_a_model,
            self.monster_b_model,
        ]

        self.cam_controller = CameraController(self.camera, self.combatants)
        self.taskMgr.add(self.cam_controller.update, 'Camera Controller')

        # UI
        self.ui = cefpanda.CEFPanda()
        self.load_ui('main')

    def load_ui(self, uiname):
        self.ui.load(os.path.join(APP_ROOT_DIR, 'ui', '{}.html'.format(uiname)))

    def move_combatant(self, index, delta):
        new_positions = [model.get_x() for model in self.combatants]

        new_position = new_positions[index] + delta
        if abs(new_position) > 10:
            print(abs(new_position))
            return

        new_positions[index] = new_position

        distance = max(new_positions) - min(new_positions)
        if distance > 8 or distance < 2:
            return

        model = self.combatants[index]
        model.set_x(model.get_x() + delta)


APP = GameApp()
APP.run()
