from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText

from .commonui import CommonUI

class TitleUI(CommonUI):
    def __init__(self, showbase):
        super().__init__(base)

        # Background Image
        self.roots.append(OnscreenImage(parent=showbase.render2d, image='backgrounds/titlebg.webm'))

        # Title
        self.roots.append(OnscreenText(
            parent=showbase.aspect2d,
            text='Mercury',
            scale=0.30,
            pos=(0, 0.75, 0.0),
            fg=(0.8, 0.8, 0.8, 1.0)
        ))

        # Move menu down
        self.menu.root.set_z(-0.5)
