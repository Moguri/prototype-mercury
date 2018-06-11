from direct.showbase.MessengerGlobal import messenger

from .gamestate import GameState
from .menuhelper import MenuHelper


class TitleState(GameState):
    def __init__(self):
        super().__init__()

        self.menu_helper = MenuHelper(self)
        self.menu_helper.menus = {
            'base': [
                ('New Game', base.change_state, ['Ranch']),
                ('Versus AI', self.versus, [True]),
                ('Versus Player', self.versus, [False]),
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

    def versus(self, use_ai):
        base.blackboard['use_ai'] = use_ai
        base.change_state('CharacterSelection')

    def quit(self):
        messenger.send('escape')
