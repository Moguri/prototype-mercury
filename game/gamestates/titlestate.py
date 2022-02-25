from direct.showbase.MessengerGlobal import messenger

from .gamestate import GameState
from .saveloadstate import saves_exist

class TitleState(GameState):
    def __init__(self):
        super().__init__()

        # UI
        self.load_ui('title')
        menu_items = []
        if saves_exist():
            menu_items += [
                ('Continue', base.change_state, ['Continue']),
                ('Load', base.change_state, ['Load', True]),
            ]
        menu_items += [
            ('New Game', base.change_state, ['NewTrainer', True]),
            ('Quit', messenger.send, ['quit']),
        ]

        self.menu_helper.set_menu('', menu_items)

        # Background Music
        self.play_bg_music('the_fall_of_arcana')
