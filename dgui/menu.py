import panda3d.core as p3d

from direct.showbase.MessengerGlobal import messenger
from direct.gui.DirectGui import DirectLabel, DirectButton, DGG

from . import settings

class Menu():
    MENU_START = 0.7
    BUTTON_WIDTH = 0.75
    BUTTON_HEIGHT = 0.15
    BUTTON_SPACING = 0
    TEXT_SCALE = settings.TEXT_SCALE
    TEXT_INACTIVE_COLOR = settings.TEXT_INACTIVE_COLOR
    TEXT_ACTIVE_COLOR = settings.TEXT_ACTIVE_COLOR
    INACTIVE_COLOR = settings.PRIMARY_COLOR
    ACTIVE_COLOR = settings.SECONDARY_COLOR

    def __init__(self, showbase):
        self.showbase = showbase
        self.menu_buttons = []
        self.root = showbase.aspect2d.attach_new_node('Menu Root')
        self.heading = None
        self._item_text = []
        self._heading_text = ''
        self._left_edge = 0

    def show(self):
        self.root.show()

    def hide(self):
        self.root.hide()

    def cleanup(self):
        self.root.remove_node()

    def update(self, statedata):
        if 'menu_items' in statedata or 'menu_heading' in statedata:
            self._item_text = statedata.get('menu_items', self._item_text)
            self._heading_text = statedata.get('menu_heading', self._heading_text)
            self.rebuild_menu(self._item_text, self._heading_text)

        if 'selection_index' in statedata:
            self.update_selection(statedata['selection_index'])

        if 'show_menu' in statedata:
            if statedata['show_menu']:
                self.root.show()
            else:
                self.root.hide()

    def update_selection(self, index):
        for button in self.menu_buttons:
            button['frameColor'] = self.INACTIVE_COLOR
            button['text_fg'] = self.TEXT_INACTIVE_COLOR
        self.menu_buttons[index]['frameColor'] = self.ACTIVE_COLOR
        self.menu_buttons[index]['text_fg'] = self.TEXT_ACTIVE_COLOR

    def build_buttons(self, items, has_heading, common_kwargs):
        return [
            DirectButton(
                pos=(
                    self._left_edge,
                    0,
                    self.MENU_START- (self.BUTTON_HEIGHT + self.BUTTON_SPACING) * (i+has_heading)
                ),
                text=item,
                text_align=p3d.TextNode.ALeft,
                **common_kwargs
            )
            for i, item in enumerate(items)
        ]

    def rebuild_menu(self, newitems, heading):
        self._left_edge = -self.showbase.get_aspect_ratio() + 0.2
        common_kwargs = {
            'parent': self.root,
            'text_scale': self.TEXT_SCALE,
            'relief': DGG.FLAT,
            'frameSize': [
                -0.05,
                self.BUTTON_WIDTH - 0.05,
                -0.05,
                self.BUTTON_HEIGHT - 0.05
            ],
        }

        has_heading = bool(heading)
        if has_heading:
            self.heading = DirectLabel(
                pos=(
                    self._left_edge,
                    0,
                    self.MENU_START
                ),
                text=heading.upper(),
                text_align=p3d.TextNode.ACenter,
                text_fg=self.TEXT_ACTIVE_COLOR,
                text_pos=(-0.05 + self.BUTTON_WIDTH/2, 0),
                **common_kwargs
            )

        for button in self.menu_buttons:
            button.remove_node()
        self.menu_buttons = self.build_buttons(newitems, has_heading, common_kwargs)

        cursor_hidden = p3d.ConfigVariableBool('cursor-hidden')

        if not cursor_hidden:
            for idx, button in enumerate(self.menu_buttons):
                def menu_hover(bid, _event):
                    messenger.send('menu-hover', [bid])
                button.bind(DGG.WITHIN, menu_hover, [idx])
                def menu_click(_event):
                    messenger.send('menu-click')
                button.bind(DGG.B1CLICK, menu_click)

        if newitems:
            self.update_selection(0)
