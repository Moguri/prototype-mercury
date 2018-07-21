import datetime
import json
import os

import jsonschema
import panda3d.core as p3d

import pathutils
from playerdata import PlayerData
from .gamestate import GameState
from .menuhelper import MenuHelper


class BaseSavesState(GameState):
    def __init__(self, do_save):
        super().__init__()

        confvar = p3d.ConfigVariableString('mercury-saves-dir', '$MAIN_DIR/saves')
        self.saves_dir = pathutils.parse_path(confvar.get_value())

        self.menu_helper = MenuHelper(self)

        self.metadata = self.collect_save_metadata(self.saves_dir)

        self.load_ui('saves')
        self.update_ui({
            'doing_save': do_save,
            'saves': self.metadata,
        })

    def cleanup(self):
        super().cleanup()

        self.menu_helper.cleanup()

    def update(self, dt):
        super().update(dt)

        self.menu_helper.update_ui()

    def collect_save_metadata(self, savesdir):
        if not savesdir.exists():
            os.makedirs(savesdir)

        metadata = [
            json.load(open(os.path.join(savesdir, filename)))
            for filename in os.listdir(savesdir)
            if filename.endswith('.meta')
        ]

        schema_name = 'savemetadata.schema.json'
        schema_path = os.path.join(pathutils.APP_ROOT_DIR, 'data', 'schemas', schema_name)
        with open(schema_path) as schema_file:
            schema = json.load(schema_file)
        _ = [jsonschema.validate(i, schema) for i in metadata]

        def sort_access_key(info):
            dtobj = datetime.datetime.strptime(info['last_access_time'], '%Y-%m-%dT%H:%M:%S.%f')
            return -dtobj.timestamp()

        return {
            i['id']: i
            for i in sorted(metadata, key=sort_access_key)
        }


class SaveState(BaseSavesState):
    def __init__(self):
        super().__init__(True)

        self.player = base.blackboard.get('player', PlayerData())

        self.menu_helper.menus = {
            'base': [
                ('Back', base.change_to_previous_state, []),
                ('New Save', self.do_save, [None]),
            ] + [
                (i, self.do_save, [i]) for i in self.metadata
            ],
        }
        self.menu_helper.set_menu('base')

    def do_save(self, saveid):
        if saveid is None:
            self.player.new_saveid()
        else:
            self.player.saveid = saveid

        savebasepath = os.path.join(self.saves_dir, self.player.saveid)
        with open(savebasepath + '.meta', 'w') as meta_file:
            json.dump(self.player.to_meta_dict(), meta_file)

        with open(savebasepath + '.save', 'w') as save_file:
            self.player.save(save_file)

        base.change_to_previous_state()


class LoadState(BaseSavesState):
    def __init__(self):
        super().__init__(False)

        self.menu_helper.menus = {
            'base': [
                ('Back', base.change_to_previous_state, []),
            ] + [
                (i, self.do_load, [i]) for i in self.metadata
            ],
        }
        self.menu_helper.set_menu('base')

    def do_load(self, saveid):
        savepath = os.path.join(self.saves_dir, saveid+'.save')
        with open(savepath) as save_file:
            player = PlayerData.load(save_file)
        player.saveid = saveid
        base.blackboard['player'] = player

        base.change_to_previous_state()
