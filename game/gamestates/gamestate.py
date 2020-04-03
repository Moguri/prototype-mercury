import json

from direct.showbase.DirectObject import DirectObject
import panda3d.core as p3d

from .menuhelper import MenuHelper


class GameState(DirectObject):
    def __init__(self):
        super().__init__()
        self.root_node = p3d.NodePath('State Root')
        self.root_node.reparent_to(base.render)
        self.menu_helper = MenuHelper(self)

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

    def update(self, _dt):
        self.menu_helper.update_ui()
