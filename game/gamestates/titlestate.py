from direct.showbase.MessengerGlobal import messenger

from .gamestate import GameState
from .menuhelper import MenuHelper


class TitleState(GameState):
    def __init__(self):
        super().__init__()

        self.menu_helper = MenuHelper(self, is_horizontal=True)
        self.menu_helper.menus = {
            'base': [
                ('New Game', base.change_state, ['NewTrainer']),
                ('Load Game', base.change_state, ['Load']),
                ('Quit', self.quit, []),
            ],
        }

        self.load_ui('title')
        self.menu_helper.set_menu('base')

    def cleanup(self):
        super().cleanup()

        self.menu_helper.cleanup()

    def update(self, dt):
        super().update(dt)

        self.menu_helper.update_ui()

    def quit(self):
        messenger.send('escape')
