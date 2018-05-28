import os
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d
import cefpanda
import blenderpanda

import eventmapper
from gamedb import GameDB
import gamestates


if hasattr(sys, 'frozen'):
    APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    APP_ROOT_DIR = p3d.Filename.from_os_specific(os.path.abspath(os.path.dirname(__file__)))
if not APP_ROOT_DIR:
    print('empty app_root_dir')
    sys.exit()


# Load config files before ShowBase is initialized
CONFIG_DIR = p3d.Filename(APP_ROOT_DIR, 'config')
p3d.load_prc_file(p3d.Filename(CONFIG_DIR, 'game.prc'))
p3d.load_prc_file(p3d.Filename(CONFIG_DIR, 'inputs.prc'))
p3d.load_prc_file(p3d.Filename(CONFIG_DIR, 'user.prc'))


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

        self.blackboard = {
            'use_ai': p3d.ConfigVariableBool('mercury-use-ai', 'False'),
        }

        self.event_mapper = eventmapper.EventMapper()

        # UI
        self.ui = cefpanda.CEFPanda()

        # Game states
        initial_state = p3d.ConfigVariableString('mercury-initial-state', 'CharacterSelection')
        self.current_state = gamestates.states[initial_state.get_value()]()
        def update_gamestate(task):
            self.current_state.update(p3d.ClockObject.get_global_clock().get_dt())
            return task.cont
        self.taskMgr.add(update_gamestate, 'GameState')

    def change_state(self, next_state):
        self.current_state.cleanup()
        self.current_state = gamestates.states[next_state]()

    def load_ui(self, uiname):
        self.ui.load(os.path.join(APP_ROOT_DIR, 'ui', '{}.html'.format(uiname)))


APP = GameApp()
APP.run()
