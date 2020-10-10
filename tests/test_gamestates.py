# pylint: disable=unused-argument
import pytest

from game import gamestates

def test_state_manager_init(app, state_manager):
    pass

@pytest.mark.parametrize('state', gamestates.states.keys())
def test_smoke(app, state_manager, state):
    state_manager.change(state)
    state_manager.update()
