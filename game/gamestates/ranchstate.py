from .gamestate import GameState


class RanchState(GameState):
    def __init__(self):
        super().__init__()

        self.menu_items = [
            ('Combat', base.change_state, ['Combat']),
        ]
        self.selection_idx = 0

        self.accept('p1-move-down', self.increment_selection)
        self.accept('p1-move-up', self.decrement_selection)
        self.accept('p1-accept', self.accept_selection)

        self.load_ui('ranch')
        self.update_ui({
            'menu_items': [i[0] for i in self.menu_items],
        })

    def update(self, dt):
        super().update(dt)

        self.update_ui({
            'selection_index': self.selection_idx,
        })

    def increment_selection(self):
        self.selection_idx += 1
        if self.selection_idx >= len(self.menu_items):
            self.selection_idx = 0

    def decrement_selection(self):
        self.selection_idx -= 1
        if self.selection_idx < 0:
            self.selection_idx = len(self.menu_items) - 1

    def accept_selection(self):
        selection = self.menu_items[self.selection_idx]
        selection[1](*selection[2])
