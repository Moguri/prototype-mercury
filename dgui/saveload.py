from direct.gui import DirectGui as dgui

from .commonui import CommonUI
from .menu import Menu


class SavesMenu(Menu):
    def __init__(self, showbase):
        super().__init__(showbase)

        self.menu_start = 0.5
        self.button_width = 2.5
        self.edge_inset = showbase.get_aspect_ratio() - 1.2

    def _save_to_str(self, item):
        if isinstance(item, str):
            return item
        return (
            f'{item.name} '
            f'(Rank: {item.rank}, Num Golems: {len(item.monsters)})'
            f'\t\tSaved: {item.last_save}\n'
        )

    def build_buttons(self, items, has_heading, common_kwargs):
        return super().build_buttons(
            [
                self._save_to_str(i)
                for i in items
            ],
            has_heading,
            common_kwargs
        )


class SaveUI(CommonUI):
    def __init__(self, showbase):
        super().__init__(showbase)

        self.roots.append(dgui.OnscreenText(
            parent=showbase.aspect2d,
            text='Save',
            scale=0.20,
            pos=(0, 0.75, 0.0),
            fg=(0.8, 0.8, 0.8, 1.0)
        ))

        self.menu = SavesMenu(showbase)


class LoadUI(CommonUI):
    def __init__(self, showbase):
        super().__init__(showbase)

        self.roots.append(dgui.OnscreenText(
            parent=showbase.aspect2d,
            text='Load',
            scale=0.20,
            pos=(0, 0.75, 0.0),
            fg=(0.8, 0.8, 0.8, 1.0)
        ))

        self.menu = SavesMenu(showbase)
