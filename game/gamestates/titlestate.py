from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.MessengerGlobal import messenger

from ..playerdata import PlayerData
from .gamestate import GameState

class TitleState(GameState):
    def __init__(self):
        super().__init__()

        # Background Image
        OnscreenImage(parent=self.root_node2d, image='titlebg.webm')

        # UI
        self.load_ui('title')
        menu_items = [
            ('Quit', messenger.send, ['quit']),
        ]
        if base.allow_saves:
            menu_items.insert(0, ('New Game', base.change_state, ['NewTrainer']))
            menu_items.insert(1, ('Load Game', base.change_state, ['Load']))
        else:
            def new_game():
                base.blackboard['player'] = PlayerData()
                base.change_state('Ranch')
            menu_items.insert(0, ('Start', new_game, []))
        self.menu_helper.set_menu('', menu_items)

        # Background Music
        self.play_bg_music('the_fall_of_arcana')
