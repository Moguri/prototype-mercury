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
    'sphinxcontrib.mermaid',
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
html_theme_options = {
    'fixed_sidebar': True,
    'github_user': 'Moguri',
    'github_repo': 'prototype-mercury',
    'extra_nav_links': {
        'Builds on itch.io': 'https://mogurijin.itch.io/mercury',
    }
}

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

stat_names = {
    'hp': 'HP',
    'physical_attack': 'Physical Attack',
    'magical_attack': 'Magical Attack',
    'movement': 'Movement',
}

def make_writer(fileobj):
    def wrap(*args, **kwargs):
        print(*args, file=fileobj, **kwargs)
    return wrap

with open(f'{gen_dir}/forms.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Forms')
    write('======\n')

    for form in sorted(gdb['forms'].values(), key=lambda x: x.name):
        if {'disabled', 'in_test'} & set(form.required_tags):
            continue
        write(f'.. _form-{form.id}:\n')
        title = f'{form.name} ({form.id})'
        write(title)
        write('-' * len(title))
        write()
        write(f'{form.description}')
        write()

        write('Starting Tags')
        write('^^^^^^^^^^^^^\n')
        if form.tags:
            for tag in form.tags:
                write(f'* ``{tag}``')
        else:
            write('None')
        write()

        write('Required Tags')
        write('^^^^^^^^^^^^^\n')
        if form.required_tags:
            for tag in form.required_tags:
                write(f'* ``{tag}``')
        else:
            write('None')
        write()

        write('Stats')
        write('^^^^^\n')
        write('.. list-table::')
        write('   :align: left')
        write()
        for stat in stat_names:
            amount = getattr(form, stat)
            write(f'   * - {stat_names[stat]}')
            write(f'     - {amount}')
        write()

        write('Mesh')
        write('^^^^\n')
        mesh = form.mesh
        write(f'``{mesh["bam_file"]}/{mesh["root_node"]}``')
        write()

with open(f'{gen_dir}/abilities.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Abilities')
    write('=========\n')

    table_items = {
        'type': 'Type',
        'power': 'Power',
        'range': 'Range',
        'hit_chance': 'Hit Chance',
    }

    for ability in sorted(gdb['abilities'].values(), key=lambda x: x.name):
        write(f'.. _ability-{ability.id}:\n')
        title = f'{ability.name} ({ability.id})'
        write(title)
        write('-' * len(title))
        write()
        write(f'{ability.description}\n')


        write('.. list-table::')
        write('   :align: left')
        write()
        for item, label in table_items.items():
            if item == 'range':
                rmin = ability.range_min
                rmax = ability.range_max
                if rmin == rmax:
                    value = rmin
                else:
                    value = f'{rmin} - {rmax}'
            else:
                value = getattr(ability, item)
            write(f'   * - {label}')
            write(f'     - {value}')
        write()

        write('Effects')
        write('^^^^^^^\n')
        write()
        for effect in ability.effects:
            write(f'* ``{effect}``')
        write()

with open(f'{gen_dir}/index.rst', 'w') as rstfile:
    write = make_writer(rstfile)

    write('Game Data')
    write('=========\n')

    write('.. toctree::')

    datamodels = [
        'forms',
        'abilities',
    ]
    for datamodel in datamodels:
        write(f'   {datamodel}.rst')
