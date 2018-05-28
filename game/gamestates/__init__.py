from .gamestate import GameState
from .combatstate import CombatState
from .characterselectionstate import CharacterSelectionState


__all__ = ['states']


#pylint: disable=invalid-name
states = {
    'Combat': CombatState,
    'CharacterSelection': CharacterSelectionState,
}
