import collections
import json
import os
import sys


if hasattr(sys, 'frozen'):
    _APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    _APP_ROOT_DIR = os.path.dirname(__file__)
if not _APP_ROOT_DIR:
    print('empty app_root_dir')
    sys.exit()


class GameDB(collections.UserDict):
    _ptr = None

    def __init__(self):
        data_dir = os.path.join(_APP_ROOT_DIR, 'data')
        super().__init__({
            'abilities': self._load_directory(os.path.join(data_dir, 'abilities')),
            'breeds': self._load_directory(os.path.join(data_dir, 'breeds')),
        })

    def _load_directory(self, dirpath):
        data_list = [
            json.load(open(os.path.join(dirpath, filename)))
            for filename in os.listdir(dirpath)
        ]
        return {
            i['id']: i
            for i in data_list
        }

    @classmethod
    def get_instance(cls):
        if cls._ptr is None:
            cls._ptr = cls()
        return cls._ptr


if __name__ == '__main__':
    import pprint
    pprint.pprint(GameDB.get_instance())
