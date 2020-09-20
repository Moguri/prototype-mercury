from direct.showbase.DirectObject import DirectObject

from .menu import Menu

class CommonUI():
    def __init__(self, showbase):
        self.roots = []
        self.showbase = showbase
        self.menu = Menu(showbase)

    def cleanup(self):
        for root in self.roots:
            root.remove_node()
        self.roots = []
        self.menu.cleanup()

    def update(self, state_data):
        self.menu.update(state_data)
