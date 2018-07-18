from playerdata import PlayerData
from .gamestate import GameState


class NewTrainerState(GameState):
    def __init__(self):
        super().__init__()

        self.load_ui('new_trainer')
        base.ui.set_js_function('submit_form', self.new_trainer)

        self.accept('p1-accept', base.ui.execute_js, ['attempt_submit()'])

    def new_trainer(self, data):
        player = PlayerData()
        player.name = data['name']

        base.blackboard['player'] = player

        base.change_state('Ranch')
