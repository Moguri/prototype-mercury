import os
from setuptools import setup

import pman.build_apps


class CustomBuildApps(pman.build_apps):
    def run(self):
        # Run regular build_apps
        super().run()

        # Do any post-build fixing/cleanup
        for platform in self.platforms:
            build_dir = os.path.join(self.build_base, platform)

            # Remove some CEF files
            locales_dir = os.path.join(build_dir, 'locales')
            for i in os.listdir(locales_dir):
                if i != 'en-US.pak':
                    os.remove(os.path.join(locales_dir, i))
            os.remove(os.path.join(build_dir, 'devtools_resources.pak'))
            os.remove(os.path.join(build_dir, 'cef_extensions.pak'))
            os.remove(os.path.join(build_dir, 'snapshot_blob.bin'))


CONFIG = pman.get_config()
APP_NAME = CONFIG['general']['name']

setup(
    name=APP_NAME,
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pylint',
        'pytest-pylint',
    ],
    cmdclass={
        'build_apps': CustomBuildApps,
    },
    options={
        'build_apps': {
            'include_patterns': [
                CONFIG['build']['export_dir']+'/**',
                'game/**',
            ],
            'exclude_patterns': [
                '**/*.py',
                '__py_cache__/**',
                'game/config/user.prc',
                'game/saves/**',
            ],
            'rename_paths': {
                CONFIG['build']['export_dir']: 'assets/',
                'game/': './',
            },
            'gui_apps': {
                APP_NAME: CONFIG['run']['main_file'],
            },
            'log_filename': '$USER_APPDATA/mercury/mercury.log',
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
