import panda3d.core as p3d

from .gamestate import GameState
from .combatstate import CombatState
from .workshopstate import WorkshopState
from .titlestate import TitleState
from .newtrainerstate import NewTrainerState
from .savesstate import SaveState, LoadState


__all__ = [
    'states',
    'StateManager',
]


#pylint: disable=invalid-name
states = {
    'Combat': CombatState,
    'Workshop': WorkshopState,
    'Title': TitleState,
    'NewTrainer': NewTrainerState,
    'Save': SaveState,
    'Load': LoadState,
}

class StateManager:
    def __init__(self, initial_state_name):
        self.current_state = None
        self.previous_state_name = ''
        self.current_state_name = ''
        self.change(initial_state_name)

    def update(self):
        self.current_state.update(p3d.ClockObject.get_global_clock().get_dt())

    def change(self, state_name):
        if state_name not in states:
            raise RuntimeError(f'Unknown state name: {state_name}')
        if self.current_state is None:
            self.previous_state_name = state_name
        else:
            self.previous_state_name = self.current_state_name
            self.current_state.cleanup()
        self.current_state_name = state_name
        self.current_state = states[state_name]()

    def change_to_previous(self):
        self.change(self.previous_state_name)
