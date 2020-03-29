# pylint: disable=unused-argument
import panda3d.core as p3d
import pytest

from game import gamestates

def test_state_manager_init(app, state_manager):
    pass

@pytest.mark.parametrize('state', gamestates.states.keys())
def test_smoke(app, state_manager, state):
    state_manager.change(state)
    state_manager.update()

def test_combat_coords(app, state_manager):
    state_manager.change('Combat')
    cstate = state_manager.current_state
    assert cstate.tile_coord_to_world(2, 2) == p3d.LVector3(4, 4, 0)
    assert cstate.tilenp_to_coord(cstate.tilenps[2][1]) == (2, 1)

    assert cstate.tile_distance((0, 0), (0, 0)) == 0
    assert cstate.tile_distance((0, 1), (0, -1)) == 2
    assert cstate.tile_distance((1, 1), (3, 3)) == 4

    assert cstate.tile_get_facing_to((0, 0), (1, 1)) == (1, 0)
    assert cstate.tile_get_facing_to((1, 1), (0, 0)) == (-1, 0)
    assert cstate.tile_get_facing_to((1, 1), (1, 3)) == (0, 1)
