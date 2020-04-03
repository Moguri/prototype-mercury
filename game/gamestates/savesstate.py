import datetime
import os

import panda3d.core as p3d

from .. import pathutils
from ..playerdata import PlayerData
from .gamestate import GameState


class BaseSavesState(GameState):
    def __init__(self, do_save):
        super().__init__()

        confvar = p3d.ConfigVariableString('mercury-saves-dir', '$MAIN_DIR/saves')
        self.saves_dir = pathutils.parse_path(confvar.get_value())
        os.makedirs(self.saves_dir, exist_ok=True)

        self.saves = [
            PlayerData.load(open(os.path.join(self.saves_dir, filename)))
            for filename in os.listdir(self.saves_dir)
        ]

        self.load_ui('saves')

        def sort_access_key(save):
            dtobj = datetime.datetime.strptime(save.last_access_time, '%Y-%m-%dT%H:%M:%S.%f')
            return -dtobj.timestamp()
        self.update_ui({
            'doing_save': do_save,
            'saves': {
                i.saveid: i.to_metadata_dict()
                for i in sorted(self.saves, key=sort_access_key)
            }
        })

class SaveState(BaseSavesState):
    def __init__(self):
        super().__init__(True)

        self.player = base.blackboard.get('player', PlayerData())

        self.menu_helper.menus = {
            'base': [
                ('Back', base.change_to_previous_state, []),
                ('New Save', self.do_save, [self.player]),
            ] + [
                (i.saveid, self.do_save, [i]) for i in self.saves
            ],
        }
        self.menu_helper.set_menu('base')

    def do_save(self, save):
        savename = '{}-{}'.format(save.name, save.saveid)
        savepath = '{}.save'.format(os.path.join(self.saves_dir, savename))
        with open(savepath, 'w') as save_file:
            save.save(save_file)

        base.change_to_previous_state()


class LoadState(BaseSavesState):
    def __init__(self):
        super().__init__(False)

        self.menu_helper.menus = {
            'base': [
                ('Back', base.change_to_previous_state, []),
            ] + [
                (i.saveid, self.do_load, [i]) for i in self.saves
            ],
        }
        self.menu_helper.set_menu('base')

    def do_load(self, save):
        base.blackboard['player'] = save
        base.change_state('Ranch')
