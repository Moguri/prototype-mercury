from direct.showbase.MessengerGlobal import messenger

from .gamestate import GameState

class TitleState(GameState):
    def __init__(self):
        super().__init__()

        # UI
        self.load_ui('title')
        self.menu_helper.set_menu('', [
            ('Start', base.change_state, ['NewTrainer', True]),
            ('Quit', messenger.send, ['quit']),
        ])

        # Background Music
        self.play_bg_music('the_fall_of_arcana')
