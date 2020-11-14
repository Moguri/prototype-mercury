import panda3d.core as p3d

from direct.gui.DirectGui import DirectLabel

from .menu import Menu
from . import settings

class CommonUI():
    def __init__(self, showbase):
        self.roots = []
        self.showbase = showbase
        self.menu = Menu(showbase)
        self.display_width = self.showbase.get_aspect_ratio() * 2

        # Message Box
        self.message_box = self.create_box(
            self.display_width * 0.9, 0.125,
            (0, -0.85)
        )
        self.message_box['frameColor'] = (
            *settings.PRIMARY_COLOR[:3], 0.8
        )
        self.message_box.hide()
        self.roots.append(self.message_box)

    def cleanup(self):
        for root in self.roots:
            root.remove_node()
        self.roots = []
        self.menu.cleanup()

    def update(self, statedata):
        self.menu.update(statedata)

        if 'message' in statedata:
            msg = statedata['message']
            if msg is not None:
                self.message_box['text'] = msg
                self.message_box.show()
            else:
                self.message_box.hide()

    def create_box(self, box_width, box_height, pos, *, box_padding=0.05, **kwargs):
        return DirectLabel(
            parent=self.showbase.aspect2d,
            pos=(pos[0], 0, pos[1]),
            text='',
            text_mayChange=True,
            text_scale=settings.TEXT_SCALE,
            text_fg=settings.TEXT_ACTIVE_COLOR,
            text_align=p3d.TextNode.ALeft,
            text_pos=(
                -box_width / 2 + box_padding,
                box_height / 2 - box_padding - settings.TEXT_SCALE / 2
            ),
            frameColor=settings.PRIMARY_COLOR,
            frameSize=(
                -box_width / 2,
                box_width / 2,
                -box_height / 2,
                box_height / 2
            ),
            **kwargs
        )
