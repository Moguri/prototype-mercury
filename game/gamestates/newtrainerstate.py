from direct.gui.OnscreenImage import OnscreenImage

from ..playerdata import PlayerData
from .gamestate import GameState


class NewTrainerState(GameState):
    def __init__(self):
        super().__init__()

        # Background Image
        OnscreenImage(parent=self.root_node2d, image='backgrounds/titlebg.webm')

        if base.allow_saves:
            # UI
            self.load_ui('new_trainer')
            base.ui.set_js_function('submit_form', self.new_trainer)
        else:
            def transition(task):
                self.new_trainer({'name': 'Foo Man'})
                return task.done
            base.taskMgr.do_method_later(0, transition, 'Transition')

    def new_trainer(self, data):
        player = PlayerData()
        player.name = data['name']

        base.blackboard['player'] = player
        base.change_state('Ranch')
