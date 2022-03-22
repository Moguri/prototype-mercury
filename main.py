import os
import sys

from direct.showbase.ShowBase import ShowBase
from direct.interval import IntervalGlobal as intervals
import panda3d.core as p3d
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
        base.enable_particles()
        gdb = gamedb.get_instance()

        # Render pipeline
        self.set_background_color((0, 0, 0, 1))
        self.render.set_antialias(p3d.AntialiasAttrib.MAuto)
        self.render_pipeline = simplepbr.init(
            max_lights=4,
            msaa_samples=p3d.ConfigVariableInt('msaa-samples', 4).get_value(),
            enable_shadows=p3d.ConfigVariableBool('enable-shadows', True).get_value(),
            exposure=5,
        )

        # Controls
        self.event_mapper = eventmapper.EventMapper()
        self.disable_mouse()
        self.accept('quit', sys.exit)
        self.accept('toggle-buffer-viewer', self.bufferViewer.toggleEnable)
        self.accept('toggle-oobe', self.oobe)
        self.accept('save-screenshot', self.screenshot)

        # Global storage
        self.blackboard = {
        }
        default_save = p3d.ConfigVariableString('mercury-default-save', '').get_value()
        if default_save:
            saveloc = os.path.join(
                pathutils.get_saves_dir(),
                default_save,
            )
            if not saveloc.endswith('.sav'):
                saveloc += '.sav'
            if os.path.exists(saveloc):
                with open(saveloc) as savefile:
                    self.blackboard['player'] = PlayerData.load(savefile)
        default_monster_id = p3d.ConfigVariableString('mercury-default-monster', '').get_value()
        if default_monster_id:
            default_monster = Monster(gdb['monsters'][default_monster_id])
        else:
            default_form = p3d.ConfigVariableString('mercury-default-form', 'mine').get_value()
            default_monster = Monster.make_new('player_monster', form_id=default_form)

        if 'player' not in self.blackboard:
            self.blackboard['player'] = PlayerData()
            self.blackboard['player'].monsters = [default_monster]

        # UI
        default_font = self.loader.load_font(
            'fonts/BalooThambi2-Medium.ttf',
            pixelsPerUnit=90
        )
        p3d.TextNode.set_default_font(default_font)

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


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
