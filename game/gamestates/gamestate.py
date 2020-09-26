from direct.showbase.DirectObject import DirectObject
import panda3d.core as p3d

import dgui

from ..menuhelper import MenuHelper


class GameState(DirectObject):
    def __init__(self):
        super().__init__()
        self.root_node = p3d.NodePath('State Root')
        self.root_node.reparent_to(base.render)
        self.root_node2d = p3d.NodePath('State Root 2D')
        self.root_node2d.reparent_to(base.render2d)
        self.dgui = None
        self.menu_helper = MenuHelper(self.update_ui)
        self._input_state = None

        def handle_fade(task):
            if base.transitions.fadeOutActive():
                base.transitions.fadeIn()
            return task.done
        base.taskMgr.do_method_later(0, handle_fade, 'Fade In')

    def cleanup(self):
        self.ignoreAll()
        self.root_node.remove_node()
        self.root_node = None
        self.root_node2d.remove_node()
        self.root_node2d = None
        base.render.clear_light()
        self.menu_helper.cleanup()
        if self.dgui:
            self.dgui.cleanup()

    def load_ui(self, name):
        self.dgui = dgui.UIS[name](base)

    def update_ui(self, state_data):
        self.dgui.update(state_data)

    def play_bg_music(self, filename):
        bgmusic = base.loader.load_music(f'music/{filename}.opus')
        bgmusic.set_loop(True)
        bgmusic.play()

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
