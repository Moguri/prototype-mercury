import collections
import json
import os
import sys

import datamodels


if hasattr(sys, 'frozen'):
    _APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    _APP_ROOT_DIR = os.path.dirname(__file__)
if not _APP_ROOT_DIR:
    print('empty app_root_dir')
    sys.exit()


class GameDB(collections.UserDict):
    _ptr = None
    data_dir = os.path.join(_APP_ROOT_DIR, 'data')
    top_level_keys = (
        ('abilities', datamodels.Ability),
        ('breeds', datamodels.Breed),
    )

    def __init__(self):
        super().__init__({
            i[0]: self._load_directory(i[1], os.path.join(self.data_dir, i[0]))
            for i in self.top_level_keys
        })

    def _load_directory(self, data_model, dirpath):
        data_list = [
            json.load(open(os.path.join(dirpath, filename)))
            for filename in os.listdir(dirpath)
        ]
        return {
            i['id']: data_model(i)
            for i in data_list
        }

    @classmethod
    def get_instance(cls):
        if cls._ptr is None:
            cls._ptr = cls()
        return cls._ptr


if __name__ == '__main__':
    print("GameDB:")
    for key, value in GameDB.get_instance().items():
        print("\t", key)
        for i in value.values():
            for j in repr(i).split('\n'):
                print("\t\t", j)
