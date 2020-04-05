# pylint: disable=unused-argument
import panda3d.core as p3d
import pytest

from game import gamestates
from game.gamestates.combatstate import Arena

def test_state_manager_init(app, state_manager):
    pass

@pytest.mark.parametrize('state', gamestates.states.keys())
def test_smoke(app, state_manager, state):
    state_manager.change(state)
    state_manager.update()

def test_combat_coords(app):
    arena = Arena(p3d.NodePath('root'), 5, 5)
    assert arena.tile_coord_to_world((2, 2)) == p3d.LVector3(4, 4, 0)
    assert arena.tilenp_to_coord(arena.tilenps[2][1]) == (2, 1)

    assert arena.tile_distance((0, 0), (0, 0)) == 0
    assert arena.tile_distance((0, 1), (0, -1)) == 2
    assert arena.tile_distance((1, 1), (3, 3)) == 4

    assert arena.tile_get_facing_to((0, 0), (1, 1)) == (1, 0)
    assert arena.tile_get_facing_to((1, 1), (0, 0)) == (-1, 0)
    assert arena.tile_get_facing_to((1, 1), (1, 3)) == (0, 1)
