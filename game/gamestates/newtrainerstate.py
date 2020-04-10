from direct.gui.OnscreenImage import OnscreenImage

from ..playerdata import PlayerData
from .gamestate import GameState


class NewTrainerState(GameState):
    def __init__(self):
        super().__init__()

        # Background Image
        OnscreenImage(parent=self.root_node2d, image='titlebg.webm')

        # UI
        self.load_ui('new_trainer')
        base.ui.set_js_function('submit_form', self.new_trainer)

    def new_trainer(self, data):
        player = PlayerData()
        player.name = data['name']

        base.blackboard['player'] = player

        base.change_state('Ranch')
