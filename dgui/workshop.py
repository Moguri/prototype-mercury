import panda3d.core as p3d

from direct.gui.DirectGui import DirectLabel
from direct.interval import IntervalGlobal as intervals

from .commonui import CommonUI
from . import settings

class WorkshopUI(CommonUI):
    def __init__(self, showbase):
        super().__init__(base)

        self.stats_box = self.create_box(
            self.display_width * 0.6, 1.7,
            (0.4, 0.1)
        )
        self.stats_box['frameColor'] = (
            *settings.PRIMARY_COLOR[:3], 0.9
        )
        self.roots.append(self.stats_box)

        # Build labels for the stat box
        common_kwargs = {
            'parent': self.stats_box,
            'text': '',
            'text_mayChange': True,
            'text_fg': settings.TEXT_ACTIVE_COLOR,
            'frameColor': (0, 0, 0, 0),
        }
        self._stats_header = DirectLabel(
            text_scale=settings.TEXT_SCALE * 1.50,
            text_align=p3d.TextNode.A_center,
            pos=(0, 0, 0.75),
            **common_kwargs
        )

        common_kwargs['text_scale'] = settings.TEXT_SCALE
        common_kwargs['text_align'] = p3d.TextNode.A_left
        self._stats_golem = DirectLabel(
            pos=(-1, 0, 0.65),
            **common_kwargs
        )
        self._stats_form = DirectLabel(
            pos=(-1, 0, 0.25),
            **common_kwargs
        )
        self._stats_weapon = DirectLabel(
            pos=(-1, 0, -0.3),
            **common_kwargs
        )

    def update(self, statedata):
        super().update(statedata)

        if 'monster' in statedata:
            self.rebuild_stats(statedata['monster'])

        if 'show_stats' in statedata:
            show = statedata['show_stats']
            if show and self.stats_box.is_hidden():
                intervals.LerpPosInterval(
                    self.stats_box,
                    0.1,
                    self.stats_box.get_pos(),
                    startPos=(
                        -1, 0, self.stats_box.get_z()
                    ),
                    blendType='easeInOut'
                ).start()
                self.stats_box.show()
            elif not show:
                self.stats_box.hide()

    def rebuild_stats(self, monsterdata):
        self._stats_header['text'] = monsterdata["name"]
        self._stats_golem['text'] = (
            f'Hit Points: {monsterdata["hit_points"]}\t'
            f'Physical Attack: {monsterdata["physical_attack"]}\n'
            f'Movement: {monsterdata["movement"]}\t'
            f'Magical Attack: {monsterdata["magical_attack"]}\n'
            'Power:'
        )
        form = monsterdata['form']
        fabilities = [
            'HP Up',
            'Mov Up',
            'PA Up',
        ]
        self._stats_form['text'] = (
            f'Form: {form["name"]}\n'
            f'  Abilities:\n'
            f'    {fabilities[0]}\n'
            f'    {fabilities[1]}\n'
            f'    {fabilities[2]}\n'
        )
        weapon = monsterdata['weapon']
        wabilities = [i.name for i in weapon['abilities']]
        while len(wabilities) < 3:
            wabilities.append('')
        self._stats_weapon['text'] = (
            f'Weapon: {weapon["name"]}\n'
            f'  Abilities:\t\tStats:\n'
            f'    {wabilities[0]:30}\t  Power: {weapon["damage"]}\n'
            f'    {wabilities[1]:30}\t  Type: {weapon["type"]}\n'
            f'    {wabilities[2]:30}\t  Range Min: {weapon["range_min"]}\n'
            f'  \t\t  Range Max: {weapon["range_max"]}\n'
        )
