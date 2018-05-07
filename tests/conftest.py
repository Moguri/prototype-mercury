#pylint:disable=redefined-outer-name
import sys
import os

import pytest

TESTDIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(TESTDIR, '..', 'game'))


@pytest.fixture
def combatant():
    import panda3d.core as p3d
    import combatant
    import gamedb

    breed = gamedb.GameDB.get_instance()['breeds']['bobcatshark']

    return combatant.Combatant(breed, p3d.NodePath(''), [])

@pytest.fixture
def dt():
    return 1/60

@pytest.fixture
def ai_controller(combatant):
    import ai
    return ai.Controller(combatant)
