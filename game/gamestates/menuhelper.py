from direct.showbase.DirectObject import DirectObject


class MenuHelper(DirectObject):
    def __init__(self, update_ui_fn):
        super().__init__()

        self.update_ui = update_ui_fn
        self.menus = {}
        self.menu_headings = {}

        self._menu_items = []
        self.selection_idx = 0
        self.lock = False
        self._show = True

        self.accept('move-down', self.move_selection, [1])
        self.accept('move-up', self.move_selection, [-1])
        self.accept('move-right', self.move_selection, [1])
        self.accept('move-left', self.move_selection, [-1])
        self.accept('accept', self.accept_selection)
        self.accept('reject', self.reject_selection)

        self.accept_cb = None
        self.reject_cb = None
        self.selection_change_cb = None

    @property
    def show(self):
        return self._show

    @show.setter
    def show(self, value):
        self._show = bool(value)
        self.update_ui({
            'show_menu': self._show,
        })

    @property
    def current_selection(self):
        return self._menu_items[self.selection_idx]

    def cleanup(self):
        self.ignoreAll()

    def move_selection(self, delta):
        if self.lock:
            return

        self.selection_idx += delta

        if self.selection_idx < 0:
            self.selection_idx = len(self._menu_items) - 1
        elif self.selection_idx >= len(self._menu_items):
            self.selection_idx = 0

        self.update_ui({
            'selection_index': self.selection_idx,
        })

        if self.selection_change_cb is not None:
            # pylint: disable=not-callable
            self.selection_change_cb(self.selection_idx)

    def accept_selection(self):
        if not self._menu_items:
            return

        if self.accept_cb is not None:
            # pylint: disable=not-callable
            result = self.accept_cb()
            if result:
                return

        if self.lock:
            return

        selection = self._menu_items[self.selection_idx]
        selection[1](*selection[2])

    def reject_selection(self):
        if not self._menu_items:
            return

        if self.reject_cb is not None:
            # pylint: disable=not-callable
            self.reject_cb()

    def set_menu(self, heading, items, *, show=True, lock=False):
        self._menu_items = items
        self.selection_idx = 0
        self.update_ui({
            'menu_heading': heading,
            'menu_items': [i[0] for i in self._menu_items],
            'selection_index': self.selection_idx,
        })
        self.show = show
        self.lock = lock
