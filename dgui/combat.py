from .commonui import CommonUI
from . import settings

class CombatUI(CommonUI):
    def __init__(self, showbase):
        super().__init__(base)

        self.message_box.set_pos((0, 0, 0.8))

        self.results_box = self.create_box(1.3, 1.0, (0, -0.2))
        self.results_box['frameColor'] = (
            *settings.PRIMARY_COLOR[:3], 0.8
        )
        self.results_box.hide()
        self.roots.append(self.results_box)

        self.status_box = self.create_box(1.0, 0.4, (1, -0.6))
        self.roots.append(self.status_box)

    def update(self, statedata):
        super().update(statedata)

        if 'results' in statedata:
            if statedata['results']:
                results = '\n'.join([
                    f'  * {result}'
                    for result in statedata['results']
                ])
                self.results_box['text'] = f'Results:\n{results}'
                self.results_box.show()
            else:
                self.results_box.hide()

        if 'monster' in statedata:
            monster = statedata['monster']
            if 'name' in monster:
                statusstr = (
                    f'{monster["name"]}\n'
                    f'HP: {monster["hp_current"]} / {monster["hp_max"]}\n'
                    f'CT: {monster["ct_current"]} / {monster["ct_max"]}\n'
                )
                self.status_box['text'] = statusstr
                self.status_box.show()
            else:
                self.status_box.hide()
