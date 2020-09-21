import os
import shutil
import sys

from setuptools import setup

import pman.build_apps

from main import USE_CEF

class CustomBuildApps(pman.build_apps.BuildApps):
    def run(self):
        # Run regular build_apps
        super().run()

        if not USE_CEF:
            return

        # Post-build cleanup and fixes
        for platform in self.platforms:
            builddir = os.path.join(self.build_base, platform)

            # Unnecessary CEF files
            shutil.rmtree(os.path.join(builddir, 'locales'))
            rmfiles = [
                'devtools_resources.pak',
                'cef_extensions.pak',
                'snapshot_blob.bin',
                'License',
                'LICENSE.txt',
            ]
            for fname in rmfiles:
                os.remove(os.path.join(builddir, fname))

            if 'linux' in platform:
                shutil.copyfile(
                    os.path.join(sys.base_prefix, 'lib', 'libpython3.7m.so.1.0'),
                    os.path.join(builddir, 'libpython3.7m.so.1.0')
                )
            elif 'win' in platform:
                rmfiles = [
                    # Remove duplicate msvcp*.dll files from cefpython3
                    'msvcp90.dll',
                    'msvcp100.dll',
                    'msvcp140.dll',

                    # Unused d3d files
                    'd3dcompiler_43.dll',
                    'd3dcompiler_47.dll',
                ]
                for fname in rmfiles:
                    os.remove(os.path.join(builddir, fname))


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
        'pytest-cov',
    ],
    cmdclass={
        'build_apps': CustomBuildApps,
    },
    options={
        'build_apps': {
            'include_patterns': [
                CONFIG['build']['export_dir']+'/**',
                'config/**',
                'data/**',
                'CREDITS.md',
                'LICENSE',
            ] + (['ui/**'] if USE_CEF else []),
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
            # 'log_filename': '$USER_APPDATA/{0}/{0}.log'.format(APP_NAME),
            'log_filename': 'runtime.log',
            'plugins': [
                'pandagl',
                'p3openal_audio',
            ],
            'include_modules': {
                APP_NAME: [
                    'direct.particles.ParticleManagerGlobal',
                ] + (['cefpanda'] if USE_CEF else [])
            },
            'exclude_modules': {
                '*': [
                    'cefpython3.cefpython_py27',
                    'cefpython3.cefpython_py34',
                    'cefpython3.cefpython_py35',
                    'cefpython3.cefpython_py36',
                ] + (['cefpanda'] if not USE_CEF else []),
            },
            'platforms': [
                'manylinux1_x86_64',
                'win_amd64',
            ],
        },
    }
)
