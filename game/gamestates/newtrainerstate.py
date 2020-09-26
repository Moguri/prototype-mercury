from ..playerdata import PlayerData
from .gamestate import GameState


class NewTrainerState(GameState):
    def __init__(self):
        super().__init__()

        def transition(task):
            self.new_trainer({'name': 'Foo Man'})
            return task.done
        base.taskMgr.do_method_later(0, transition, 'Transition')

    def new_trainer(self, data):
        player = PlayerData()
        player.name = data['name']

        base.blackboard['player'] = player
        base.change_state('Workshop')
