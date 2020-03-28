#pylint:disable=redefined-outer-name,import-outside-toplevel
import sys
import os

import pytest

TESTDIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(TESTDIR, '..', 'game'))


@pytest.fixture
def gdb():
    from game import gamedb
    return gamedb.get_instance()


@pytest.fixture
def monster():
    from game.monster import Monster
    return Monster.make_new('id', 'test', 'bobcatshark')

@pytest.fixture
def empty_nodepath():
    import panda3d.core as p3d
    return p3d.NodePath('empty')

@pytest.fixture
def combatant(monster, empty_nodepath):
    from game import combatant
    return combatant.Combatant(monster, empty_nodepath, [])

@pytest.fixture
def dt():
    return 1/60

@pytest.fixture
def ai_controller(combatant):
    from game import ai
    return ai.Controller(combatant)

@pytest.fixture
def player():
    from game import playerdata
    from game import gamedb

    player = playerdata.PlayerData()
    player.monster = list(gamedb.get_instance()['monsters'].values())[0]

    return player
