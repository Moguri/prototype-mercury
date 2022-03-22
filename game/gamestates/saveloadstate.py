import os

from .gamestate import GameState
from .. import pathutils
from ..playerdata import PlayerData


def get_saves():
    savesdir = pathutils.get_saves_dir()
    if not os.path.exists(savesdir):
        return []

    saves = [
        PlayerData.load(open(os.path.join(savesdir, savepath)))
        for savepath in os.listdir(savesdir)
        if savepath.endswith('.sav')
    ]

    saves = sorted(saves, key=lambda save: save.last_save, reverse=True)
    return saves


def saves_exist():
    return bool(get_saves())


class SaveState(GameState):
    def __init__(self):
        super().__init__()

        self.player = base.blackboard['player']

        # UI
        self.load_ui('save')
        self.reload_menu()

    def reload_menu(self):
        menu_items = [
            ('Back', base.change_to_previous_state, []),
            ('New', self.new_save, []),
        ] + [
            (i, self.save, [i.saveid])
            for i in get_saves()
        ]
        self.menu_helper.set_menu('', menu_items)

    def new_save(self):
        self.player.newid()
        self.save(self.player.saveid)

    def save(self, saveid):
        savesdir = pathutils.get_saves_dir()
        saveloc = os.path.join(savesdir, f'{saveid}.sav')
        os.makedirs(savesdir, exist_ok=True)
        with open(saveloc, 'w') as savefile:
            self.player.save(savefile)
        base.change_to_previous_state()


class LoadState(GameState):
    def __init__(self):
        super().__init__()

        # UI
        self.load_ui('load')
        menu_items = [
            ('Back', base.change_to_previous_state, []),
        ] + [
            (i, self.load, [i])
            for i in get_saves()
        ]
        self.menu_helper.set_menu('', menu_items)

    def load(self, savedata):
        base.blackboard['player'] = savedata
        base.change_state('Workshop')


class ContinueState(GameState):
    def __init__(self):
        super().__init__()

        def transition(task):
            savedata = get_saves()[0]
            base.blackboard['player'] = savedata
            base.change_state('Workshop')
            return task.done
        base.taskMgr.do_method_later(0, transition, 'Transition')
