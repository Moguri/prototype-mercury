import appdirs
import panda3d.core as p3d


APP_ROOT_DIR = p3d.Filename.expand_from('$MAIN_DIR')
CONFIG_DIR = p3d.Filename(APP_ROOT_DIR, 'config')

_APPNAME = 'mercury'
_APPAUTHOR = False
_APPDIRS = appdirs.AppDirs(appname=_APPNAME, appauthor=_APPAUTHOR, roaming=True)
_PATH_VARS = {
    '$USER_APPDATA': _APPDIRS.user_data_dir,
    '$MAIN_DIR': str(APP_ROOT_DIR),
}
def parse_path(path):
    path = str(path)
    path_parts = path.split('/')

    path_parts = [
        _PATH_VARS.get(i, i)
        for i in path_parts
    ]

    return p3d.Filename('/'.join(path_parts))
