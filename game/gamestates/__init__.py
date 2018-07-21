from .gamestate import GameState
from .combatstate import CombatState
from .characterselectionstate import CharacterSelectionState
from .ranchstate import RanchState
from .titlestate import TitleState
from .newtrainerstate import NewTrainerState
from .savesstate import SaveState, LoadState


__all__ = ['states']


#pylint: disable=invalid-name
states = {
    'Combat': CombatState,
    'CharacterSelection': CharacterSelectionState,
    'Ranch': RanchState,
    'Title': TitleState,
    'NewTrainer': NewTrainerState,
    'Save': SaveState,
    'Load': LoadState,
}
