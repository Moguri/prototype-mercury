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
        'build_apps': pman.build_apps.BuildApps,
    },
    options={
        'build_apps': {
            'include_patterns': [
                CONFIG['build']['export_dir']+'/**',
                'config/**',
                'data/**',
                'ui/**',
            ],
            'exclude_patterns': [
                'config/user.prc',
            ],
            'rename_paths': {
                CONFIG['build']['export_dir']: 'assets/',
            },
            'package_data_dirs': {
                'simplepbr': [
                    ('simplepbr/*.vert', '', {}),
                    ('simplepbr/*.frag', '', {}),
                ],
            },
            'gui_apps': {
                APP_NAME: CONFIG['run']['main_file'],
            },
            'log_filename': '$USER_APPDATA/{0}/{0}.log'.format(APP_NAME),
            'plugins': [
                'pandagl',
                'p3openal_audio',
            ],
            'exclude_modules': {
                '*': [
                    'cefpython3.cefpython_py27',
                    'cefpython3.cefpython_py34',
                    'cefpython3.cefpython_py35',
                    'cefpython3.cefpython_py36',
                ],
            },
            'platforms': [
                'manylinux1_x86_64',
                'win_amd64',
            ],
        },
    }
)
