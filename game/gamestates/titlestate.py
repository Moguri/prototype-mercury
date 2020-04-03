from direct.showbase.MessengerGlobal import messenger

from .gamestate import GameState

class TitleState(GameState):
    def __init__(self):
        super().__init__()

        self.load_ui('title')
        self.menu_helper.set_menu('', [
            ('New Game', base.change_state, ['NewTrainer']),
            ('Load Game', base.change_state, ['Load']),
            ('Quit', self.quit, []),
        ])

    def quit(self):
        messenger.send('escape')
