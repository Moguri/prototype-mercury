# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'Mercury'
copyright = '2020, Mercury Contributors'
author = ''


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Generate pages for data files -------------------------------------------
import shutil

from game.gamedb import GameDB

gen_dir = '_gen'

shutil.rmtree(gen_dir, ignore_errors=True)
os.makedirs(gen_dir)

GameDB.root_dir = os.path.abspath('..')
GameDB.data_dir = os.path.join(GameDB.root_dir, 'data')
GameDB.schema_dir = os.path.join(GameDB.data_dir, 'schemas')
gdb = GameDB.get_instance()

def make_writer(fileobj):
    def wrap(*args, **kwargs):
        print(*args, file=fileobj, **kwargs)
    return wrap

with open(f'{gen_dir}/breeds.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Breeds')
    write('======\n')

    for breed in sorted(gdb['breeds'].values(), key=lambda x: x.name):
        if {'disabled', 'in_test'} & set(breed.required_tags):
            continue
        write(f'.. _breed-{breed.id}:\n')
        write(breed.name)
        write('^'*len(breed.name))
        write()

        for prop, value in breed.to_dict().items():
            if prop in ('name', 'id'):
                continue
            write(f'* {prop}: {value}')
        write()

with open(f'{gen_dir}/jobs.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Jobs')
    write('====\n')

    for job in sorted(gdb['jobs'].values(), key=lambda x: x.name):
        if {'disabled', 'in_test'} & set(job.required_tags):
            continue
        write(f'.. _job-{job.id}:\n')
        write(job.name)
        write('^'*len(job.name))
        write()

        for prop, value in job.to_dict().items():
            if prop in ('name', 'id'):
                continue
            write(f'* {prop}: {value}')
        write()

with open(f'{gen_dir}/abilities.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Abilities')
    write('=========\n')

    for ability in sorted(gdb['abilities'].values(), key=lambda x: x.name):
        write(f'.. _ability-{ability.id}:\n')
        write(ability.name)
        write('^'*len(ability.name))
        write()

        for prop, value in ability.to_dict().items():
            if prop in ('name', 'id'):
                continue
            write(f'* {prop}: {value}')
        write()

with open(f'{gen_dir}/index.rst', 'w') as rstfile:
    write = make_writer(rstfile)

    write('Game Data')
    write('=========\n')

    write('.. toctree::')

    datamodels = [
        'breeds',
        'jobs',
        'abilities',
    ]
    for datamodel in datamodels:
        write(f'   {datamodel}.rst')
