from direct.showbase.MessengerGlobal import messenger

from .gamestate import GameState

class TitleState(GameState):
    def __init__(self):
        super().__init__()

        # UI
        self.load_ui('title')
        menu_items = [
            ('Quit', messenger.send, ['quit']),
        ]
        if base.allow_saves:
            menu_items.insert(0, ('New Game', base.change_state, ['NewTrainer', True]))
            menu_items.insert(1, ('Load Game', base.change_state, ['Load']))
        else:
            menu_items.insert(0, ('Start', base.change_state, ['NewTrainer', True]))
        self.menu_helper.set_menu('', menu_items)

        # Background Music
        self.play_bg_music('the_fall_of_arcana')
