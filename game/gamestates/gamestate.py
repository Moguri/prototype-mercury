import json

from direct.showbase.DirectObject import DirectObject
import panda3d.core as p3d


class GameState(DirectObject):
    def __init__(self):
        super().__init__()
        self.root_node = p3d.NodePath('State Root')
        self.root_node.reparent_to(base.render)

    def cleanup(self):
        self.ignoreAll()
        self.root_node.remove_node()
        self.root_node = None

    def load_ui(self, name):
        base.load_ui(name)

    def update_ui(self, state_data):
        base.ui.execute_js('update_state({})'.format(json.dumps(state_data)), onload=True)

    def update(self, _dt):
        pass
