import weakref

from direct.showbase.DirectObject import DirectObject


class MenuHelper(DirectObject):
    def __init__(self, state, accept_cb=None, reject_cb=None):
        super().__init__()

        self.state = weakref.proxy(state)
        self.menus = {}
        self.menu_headings = {}

        self.current_menu = ''
        self.menu_items = []
        self.selection_idx = 0
        self.lock = False
        self._show = True

        self.accept('move-down', self.move_selection, [1])
        self.accept('move-up', self.move_selection, [-1])
        self.accept('move-right', self.move_selection, [1])
        self.accept('move-left', self.move_selection, [-1])
        self.accept('accept', self.accept_selection)
        self.accept('reject', self.reject_selection)

        self.accept_cb = accept_cb
        self.reject_cb = reject_cb
        self.selection_change_cb = None

    @property
    def show(self):
        return self._show

    @show.setter
    def show(self, value):
        self._show = bool(value)
        self.state.update_ui({
            'show_menu': self._show,
        })

    @property
    def current_selection(self):
        return self.menu_items[self.selection_idx]

    def cleanup(self):
        self.ignoreAll()

    def update_ui(self):
        self.state.update_ui({
            'selection_index': self.selection_idx,
        })

    def move_selection(self, delta):
        if self.lock:
            return

        self.selection_idx += delta

        if self.selection_idx < 0:
            self.selection_idx = len(self.menu_items) - 1
        elif self.selection_idx >= len(self.menu_items):
            self.selection_idx = 0

        if self.selection_change_cb is not None:
            # pylint: disable=not-callable
            self.selection_change_cb(self.selection_idx)

    def accept_selection(self):
        if not self.menu_items:
            return

        if self.accept_cb:
            result = self.accept_cb()
            if result:
                return

        if self.lock:
            return

        selection = self.menu_items[self.selection_idx]
        selection[1](*selection[2])

    def reject_selection(self):
        if not self.menu_items:
            return

        if self.reject_cb:
            self.reject_cb()

    def set_menu(self, new_menu):
        if new_menu is '':
            return

        self.current_menu = new_menu
        self.menu_items = self.menus[new_menu]
        self.selection_idx = 0
        self.state.update_ui({
            'menu_heading': self.menu_headings.get(new_menu, ''),
            'menu_items': [i[0] for i in self.menu_items],
        })
