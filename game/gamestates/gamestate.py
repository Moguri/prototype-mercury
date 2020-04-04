import json

from direct.showbase.DirectObject import DirectObject
import panda3d.core as p3d

from ..menuhelper import MenuHelper


class GameState(DirectObject):
    def __init__(self):
        super().__init__()
        self.root_node = p3d.NodePath('State Root')
        self.root_node.reparent_to(base.render)
        self.menu_helper = MenuHelper(self.update_ui)
        self._input_state = None

    def cleanup(self):
        self.ignoreAll()
        self.root_node.remove_node()
        self.root_node = None
        base.render.clear_light()
        self.menu_helper.cleanup()

    def load_ui(self, name):
        base.load_ui(name)

    def update_ui(self, state_data):
        base.ui.execute_js('update_state({})'.format(json.dumps(state_data)), onload=True)

    def set_input_state(self, _next_state):
        self.ignore_all()
        self.menu_helper.show = False
        self.menu_helper.lock = True
        self.menu_helper.selection_idx = 0
        self.menu_helper.accept_cb = None
        self.menu_helper.reject_cb = None
        self.menu_helper.selection_change_cb = None

    @property
    def input_state(self):
        return self._input_state

    @input_state.setter
    def input_state(self, value):
        self.set_input_state(value)

    def update(self, _dt):
        pass
