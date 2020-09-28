from .commonui import CommonUI
from . import settings

class WorkshopUI(CommonUI):
    def __init__(self, showbase):
        super().__init__(base)

        self.stats_box = self.create_box(1.8, 1.25, (0, -0.25))
        self.stats_box['frameColor'] = (
            *settings.PRIMARY_COLOR[:3], 0.8
        )
        self.roots.append(self.stats_box)

    def update(self, statedata):
        super().update(statedata)

        if 'monster' in statedata:
            self.rebuild_stats(statedata['monster'])

        if 'show_stats' in statedata and self.stats_box:
            if statedata['show_stats']:
                self.stats_box.show()
            else:
                self.stats_box.hide()

    def rebuild_stats(self, monsterdata):
        self.stats_box['text'] = (
            f'Form: {monsterdata["form"]}\n'
            f'Job: {monsterdata["job"]}\n'
            f'HP: {monsterdata["hit_points"]}\n'
            f'EP: {monsterdata["ep"]}\n'
            f'Phys. Attack: {monsterdata["physical_attack"]}\n'
            f'Mag. Attack: {monsterdata["magical_attack"]}\n'
            f'Movement: {monsterdata["movement"]}\n'
        )
