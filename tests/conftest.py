#pylint:disable=redefined-outer-name,import-outside-toplevel
import sys
import os

from unittest.mock import MagicMock

import panda3d.core as p3d
from direct.interval import IntervalGlobal as intervals
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
    return p3d.NodePath('empty')

@pytest.fixture
def combatant(monster, empty_nodepath):
    from game import combatant
    return combatant.Combatant(monster, empty_nodepath)

@pytest.fixture
def dt():
    return 1/60

@pytest.fixture
def player(monster):
    from game import playerdata

    player = playerdata.PlayerData()
    player.personal_tags.add('in_test')
    player.monsters.append(monster)

    return player

@pytest.fixture
def combat():
    class Combat:
        def move_combatant_to_tile(self, *_args, **_kwargs):
            return intervals.Sequence()
        def move_combatant_to_range(self, *_args, **_kwargs):
            return intervals.Sequence()
    return Combat()

@pytest.fixture
def state_manager():
    from game.gamestates import StateManager
    return StateManager('Title')

@pytest.fixture(scope='session')
def app():
    from direct.showbase.ShowBase import ShowBase
    import pman.shim
    from game import playerdata
    from game.monster import Monster

    p3d.load_prc_file_data(
        '',
        'window-type none\n'
        'framebuffer-hardware false\n'
        'mercury-disable-music true\n'
    )
    class DummyApp(ShowBase):
        def __init__(self):
            super().__init__(self)
            pman.shim.init(self)
            player = playerdata.PlayerData()
            self.blackboard = {
                'player': player,
            }
            default_monster = Monster.make_new('player_monster', 'Default', 'claygolem')
            self.blackboard['player'].monsters = [default_monster]
            self.camera = p3d.NodePath('camera')
            self.allow_saves = False
            class Pipeline:
                def __init__(self):
                    self.exposure = 6
            self.render_pipeline = Pipeline()

            self.ui = MagicMock()
            self.event_mapper = MagicMock()

        def change_state(self, next_state):
            pass
        def change_to_previous_state(self):
            pass
        def load_ui(self, uiname):
            pass
    return DummyApp()
