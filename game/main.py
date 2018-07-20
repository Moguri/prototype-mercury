import os
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d
import cefpanda
import blenderpanda

import eventmapper
import gamedb
import gamestates
import pathutils
from playerdata import PlayerData


# Load config files before ShowBase is initialized
p3d.load_prc_file(p3d.Filename(pathutils.CONFIG_DIR, 'game.prc'))
p3d.load_prc_file(p3d.Filename(pathutils.CONFIG_DIR, 'inputs.prc'))
p3d.load_prc_file(p3d.Filename(pathutils.CONFIG_DIR, 'user.prc'))


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        gamedb.get_instance()

        self.win.set_close_request_event('escape')
        self.accept('escape', sys.exit)

        self.disable_mouse()
        self.render.set_shader_auto()
        self.render.set_antialias(p3d.AntialiasAttrib.MAuto)

        self.blackboard = {
            'use_ai': p3d.ConfigVariableBool('mercury-use-ai', 'True'),
            'player': PlayerData(),
        }

        self.event_mapper = eventmapper.EventMapper()

        # UI
        self.ui = cefpanda.CEFPanda()
        self.ui.use_mouse = False

        # Game states
        initial_state = p3d.ConfigVariableString('mercury-initial-state', 'Title')
        initial_state = initial_state.get_value()
        self.previous_state_name = self.current_state_name = initial_state
        self.current_state = gamestates.states[initial_state]()
        def update_gamestate(task):
            self.current_state.update(p3d.ClockObject.get_global_clock().get_dt())
            return task.cont
        self.taskMgr.add(update_gamestate, 'GameState')

    def change_state(self, next_state):
        self.current_state.cleanup()
        self.previous_state_name = self.current_state_name
        self.current_state_name = next_state
        self.current_state = gamestates.states[next_state]()

    def change_to_previous_state(self):
        self.change_state(self.previous_state_name)

    def load_ui(self, uiname):
        self.ui.load(os.path.join(pathutils.APP_ROOT_DIR, 'ui', '{}.html'.format(uiname)))


APP = GameApp()
APP.run()
