import os
import sys

from direct.showbase.ShowBase import ShowBase
from direct.interval import IntervalGlobal as intervals
import panda3d.core as p3d
import cefpanda
import pman.shim
import eventmapper
import simplepbr

from game import gamedb
from game import gamestates
from game import pathutils
from game.playerdata import PlayerData
from game.monster import Monster


# Load config files before ShowBase is initialized
p3d.load_prc_file(p3d.Filename(pathutils.CONFIG_DIR, 'game.prc'))
p3d.load_prc_file(p3d.Filename(pathutils.CONFIG_DIR, 'inputs.prc'))
p3d.load_prc_file(p3d.Filename(pathutils.USER_CONFIG_DIR, 'user.prc'))
p3d.load_prc_file(p3d.Filename(pathutils.CONFIG_DIR, 'user.prc'))


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        gamedb.get_instance()

        # Render pipeline
        self.render.set_antialias(p3d.AntialiasAttrib.MAuto)
        self.render_pipeline = simplepbr.init(
            msaa_samples=p3d.ConfigVariableInt('msaa-samples', 4).get_value(),
            enable_shadows=p3d.ConfigVariableBool('enable-shadows', True).get_value(),
            exposure=6,
        )

        # Controls
        self.event_mapper = eventmapper.EventMapper()
        self.disable_mouse()
        self.accept('quit', sys.exit)
        self.accept('toggle-buffer-viewer', self.bufferViewer.toggleEnable)
        self.accept('toggle-oobe', self.oobe)
        self.accept('save-screenshot', self.screenshot)

        # Global storage
        self.allow_saves = p3d.ConfigVariableBool('mercury-allow-saves', False)
        self.blackboard = {
            'player': PlayerData(),
        }
        default_breed = p3d.ConfigVariableString('mercury-default-breed', 'clay').get_value()
        default_monster = Monster.make_new('player_monster', breed_id=default_breed)
        self.blackboard['player'].monsters = [default_monster]

        # UI
        self.ui = cefpanda.CEFPanda()
        self.ui.use_mouse = False

        # Game states
        initial_state = p3d.ConfigVariableString('mercury-initial-state', 'Title').get_value()
        self.gman = gamestates.StateManager(initial_state)
        def update_state(task):
            self.gman.update()
            return task.cont
        self.taskMgr.add(update_state, 'GameState Update')

        # Get volume levels from config
        self.musicManager.set_volume(
            p3d.ConfigVariableDouble('audio-music-volume', 1.0).get_value()
        )
        self.sfxManagerList[0].set_volume(
            p3d.ConfigVariableDouble('audio-sfx-volume', 1.0).get_value()
        )

    def change_state(self, next_state, skip_fade=False):
        ival = intervals.Func(self.gman.change, next_state)
        if skip_fade:
            ival.start()
        else:
            self.transitions.fadeOut(
                finishIval=ival
            )

    def change_to_previous_state(self, skip_fade=False):
        ival = intervals.Func(self.gman.change_to_previous)
        if skip_fade:
            ival.start()
        else:
            self.transitions.fadeOut(
                finishIval=ival
            )

    def load_ui(self, uiname):
        self.ui.load_file(p3d.Filename.expand_from(f'$MAIN_DIR/ui/{uiname}.html'))


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
