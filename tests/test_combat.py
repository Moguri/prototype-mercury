# pylint: disable=unused-argument,redefined-outer-name
import pytest

import panda3d.core as p3d

from game.gamestates.combatstate import Arena

@pytest.fixture
def combatstate(state_manager, app):
    state_manager.change('Combat')
    return state_manager.current_state

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

def test_knockback_stays_in_bounds(combatstate, combatant, target):
    combatant.tile_position = (0, 2)
    target.tile_position = (0, 1)

    pos = combatstate.find_tile_at_range(target, combatant, 3)
    assert pos == (0, 0)

def test_knockback_push_into(combatstate, combatant, target, bystander):
    combatant.tile_position = (0, 3)
    target.tile_position = (0, 2)
    bystander.tile_position = (0, 0)

    combatstate.player_combatants = [
        combatant,
        target,
        bystander
    ]
    combatstate.enemy_combatants = []

    pos = combatstate.find_tile_at_range(target, combatant, 2)
    assert pos == (0, 1)

    pos = combatstate.find_tile_at_range(target, combatant, 3)
    assert pos == (0, 1)

def test_knockback_pull_into(combatstate, combatant, target, bystander):
    combatant.tile_position = (0, 3)
    target.tile_position = (0, 0)
    bystander.tile_position = (0, 2)

    combatstate.player_combatants = [
        combatant,
        target,
        bystander
    ]
    combatstate.enemy_combatants = []

    pos = combatstate.find_tile_at_range(target, combatant, 2)
    assert pos == (0, 1)

    pos = combatstate.find_tile_at_range(target, combatant, 1)
    assert pos == (0, 1)
