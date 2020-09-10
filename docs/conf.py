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
    'mp': 'MP',
    'physical_attack': 'Physical Attack',
    'magical_attack': 'Magical Attack',
    'movement': 'Movement',
}

def make_writer(fileobj):
    def wrap(*args, **kwargs):
        print(*args, file=fileobj, **kwargs)
    return wrap

with open(f'{gen_dir}/jobs_chart.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Jobs Chart')
    write('==========\n')

    for breed in sorted(gdb['breeds'].values(), key=lambda x: x.name):
        if {'disabled', 'in_test'} & set(breed.required_tags):
            continue

        title = breed.name
        write(title)
        write('-' * len(title))
        write()
        write('\n.. mermaid::')
        write('   :align: center\n')
        write('   graph LR')

        breed_tags = set(breed.tags) | {f'breed_{breed.id}'}
        for job in gdb['jobs'].values():
            non_job_tags = set([i for i in job.required_tags if not i.startswith('job_')])
            if not non_job_tags.issubset(breed_tags):
                continue
            required_jobs = [
                i.replace('job_', '').rsplit('_', 1)
                for i in job.required_tags
                if i.startswith('job_')
            ]
            # available_jobs[job.id] = required_jobs
            for rjob, level in required_jobs:
                write(f'   {rjob} -- {level} --> {job.id}["{job.name}"]')
            write(f'   {job.id}["{job.name}"]')

        write()


with open(f'{gen_dir}/breeds.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Breeds')
    write('======\n')

    for breed in sorted(gdb['breeds'].values(), key=lambda x: x.name):
        if {'disabled', 'in_test'} & set(breed.required_tags):
            continue
        write(f'.. _breed-{breed.id}:\n')
        title = f'{breed.name} ({breed.id})'
        write(title)
        write('-' * len(title))
        write()
        write(f'{breed.description}')

        write('Default Job')
        write('^^^^^^^^^^^\n')
        write(f':ref:`job-{breed.default_job.id}`')
        write()

        write('Starting Tags')
        write('^^^^^^^^^^^^^\n')
        if breed.tags:
            for tag in breed.tags:
                write(f'* ``{tag}``')
        else:
            write('None')
        write()

        write('Required Tags')
        write('^^^^^^^^^^^^^\n')
        if breed.required_tags:
            for tag in breed.required_tags:
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
            amount = getattr(breed, stat)
            write(f'   * - {stat_names[stat]}')
            write(f'     - {amount}')
        write()

        write('Skins')
        write('^^^^^\n')
        default_skin = breed.skins['default']
        skins = dict(filter(lambda x: x[0] != 'default', breed.skins.items()))
        write(f'Default: ``{default_skin["bam_file"]}/{default_skin["root_node"]}``')
        write()
        write('Others:')
        if skins:
            write()
            for jobname, skin in skins.items():
                write(f'* :ref:`job-{jobname}`: ``{skin["bam_file"]}/{skin["root_node"]}``')
        else:
            write('None')
        write()

with open(f'{gen_dir}/jobs.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Jobs')
    write('====\n')

    for job in sorted(gdb['jobs'].values(), key=lambda x: x.name):
        if {'disabled', 'in_test'} & set(job.required_tags):
            continue
        write(f'.. _job-{job.id}:\n')
        title = f'{job.name} ({job.id})'
        write(title)
        write('-' * len(title))
        write()
        write(f'{job.description}\n')

        write('Required Tags')
        write('^^^^^^^^^^^^^\n')
        if job.required_tags:
            for tag in job.required_tags:
                write(f'* ``{tag}``')
        else:
            write('None')
        write()

        write('Stat Offsets')
        write('^^^^^^^^^^^^\n')
        write('.. list-table::')
        write('   :align: left')
        write()
        for stat in stat_names:
            offset = getattr(job, f'{stat}_offset')
            write(f'   * - {stat_names[stat]}')
            write(f'     - {offset:+}')
        write()

        write('Stat Upgrades')
        write('^^^^^^^^^^^^^\n')
        write('.. list-table::')
        write('   :align: left')
        write()
        for stat in stat_names:
            num_upgrades = job.stat_upgrades.get(stat, None)
            write(f'   * - {stat_names[stat]}')
            write(f'     - {num_upgrades}')
        write()

        write('Abilities')
        write('^^^^^^^^^\n')
        write(f'Basic Attack: :ref:`ability-{job.basic_attack.id}`')
        write()
        write('Learned:')
        if job.abilities:
            write()
            for ability in job.abilities:
                write(f'* :ref:`ability-{ability}`')
        else:
            write('None')

        write()

with open(f'{gen_dir}/abilities.rst', 'w') as rstfile:
    write = make_writer(rstfile)
    write('Abilities')
    write('=========\n')

    table_items = {
        'jp_cost': 'JP',
        'mp_cost': 'MP',
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
            if item is 'range':
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
    write('   jobs_chart.rst')

    datamodels = [
        'breeds',
        'jobs',
        'abilities',
    ]
    for datamodel in datamodels:
        write(f'   {datamodel}.rst')
