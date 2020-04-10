from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.MessengerGlobal import messenger

from .gamestate import GameState

class TitleState(GameState):
    def __init__(self):
        super().__init__()

        # Background Image
        OnscreenImage(parent=self.root_node2d, image='titlebg.webm')

        # UI
        self.load_ui('title')
        self.menu_helper.set_menu('', [
            ('New Game', base.change_state, ['NewTrainer']),
            ('Load Game', base.change_state, ['Load']),
            ('Quit', messenger.send, ['quit']),
        ])

        # Background Music
        self.play_bg_music('the_fall_of_arcana')
