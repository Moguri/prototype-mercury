from .gamestate import GameState


class RanchState(GameState):
    def update(self, dt):
        super().update(dt)

        base.change_state('CharacterSelection')
