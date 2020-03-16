from setuptools import setup

import pman.build_apps


CONFIG = pman.get_config()
APP_NAME = CONFIG['general']['name']

setup(
    name=APP_NAME,
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pylint~=2.4.0',
        'pytest-pylint',
    ],
    cmdclass={
        'build_apps': pman.build_apps,
    },
    options={
        'build_apps': {
            'include_patterns': [
                CONFIG['build']['export_dir']+'/**',
                'config',
                'data',
                'ui',
            ],
            'exclude_patterns': [
                '**/*.py',
                '__py_cache__/**',
                'game/config/user.prc',
            ],
            'rename_paths': {
                CONFIG['build']['export_dir']: 'assets/',
            },
            'gui_apps': {
                APP_NAME: CONFIG['run']['main_file'],
            },
            'log_filename': '$USER_APPDATA/{0}/{0}.log'.format(APP_NAME),
            'plugins': [
                'pandagl',
                'p3openal_audio',
            ],
            'include_modules': {
                '*': [
                    'configparser',
                    'gamestates.*.*',
                ],
            },
            'exclude_modules': {
                '*': [
                    'cefpython3.cefpython_py27',
                    'cefpython3.cefpython_py34',
                    'cefpython3.cefpython_py35',
                ],
            },
            'platforms': [
                'manylinux1_x86_64',
                'win_amd64',
            ],
        },
    }
)
