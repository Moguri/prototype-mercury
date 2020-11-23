import panda3d.core as p3d

from direct.gui.DirectGui import DirectLabel, DirectButton
from direct.interval import IntervalGlobal as intervals

from .commonui import CommonUI
from .menu import Menu
from . import settings

class WorkshopUI(CommonUI):
    def __init__(self, showbase):
        super().__init__(base)

        self.num_golems_label = self.create_box(
            0, 0,
            (self.display_width / 2 -0.1, 0.95),
            box_padding=0,
            text_scale=settings.TEXT_SCALE * 1.50,
            text_align=p3d.TextNode.A_right,
            frameColor=(0, 0, 0, 0),
        )
        self.roots.append(self.num_golems_label)

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
        self._stats_menu = Menu(showbase)
        self._stats_num_fabilities = 0
        self._stats_num_wabilities = 0
        self._stats_menu.build_buttons = self._stats_build_buttons
        self._stats_menu.inactive_color = common_kwargs['frameColor']
        self._stats_menu.active_color = (
            *settings.SECONDARY_COLOR[:3], 0.9
        )
        self._stats_menu.button_width = 0.5
        self._stats_menu.button_height = 0.125

    def cleanup(self):
        super().cleanup()
        self.menu.cleanup()

    def update(self, statedata):
        if not self.stats_box.is_hidden():
            self._stats_menu.update(statedata)
            statedata.pop('show_menu', None)
        super().update(statedata)

        if 'num_form_abilities' in statedata:
            self._stats_num_fabilities = statedata['num_form_abilities']

        if 'num_weapon_abilities' in statedata:
            self._stats_num_wabilities = statedata['num_weapon_abilities']

        if 'num_golems' in statedata or 'max_golems' in statedata:
            self.num_golems_label['text'] = f'Golems: {statedata["num_golems"]}/{statedata["max_golems"]}'

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
                self.menu.hide()
                self.num_golems_label.hide()
            elif not show:
                self.stats_box.hide()
                self.menu.show()
                self.num_golems_label.show()

    def _stats_build_buttons(self, items, _has_heading, common_kwargs):
        common_kwargs['parent'] = self.stats_box
        common_kwargs['text_align'] = p3d.TextNode.A_left
        button_height = self._stats_menu.button_height
        button_spacing = self._stats_menu.button_spacing
        common_kwargs['frameSize'][2] = -0.025

        add_power_item = items[0]
        fability_items = items[1:self._stats_num_fabilities+1]
        change_weapon_item = items[self._stats_num_fabilities+1]
        wability_items = items[
            self._stats_num_fabilities+2:len(items)
        ]

        buttons = []

        for idx, item in enumerate(fability_items):
            buttons.append(
                DirectButton(
                    pos=(
                        -0.95,
                        0,
                        0.07 - (button_height + button_spacing) * idx
                    ),
                    text=item,
                    **common_kwargs
                )
            )

        buttons.append(
            DirectButton(
                pos=(-0.7, 0, -0.3),
                text=change_weapon_item,
                **common_kwargs
            )
        )

        for idx, item in enumerate(wability_items):
            buttons.append(
                DirectButton(
                    pos=(
                        -0.95,
                        0,
                        -0.5 - (button_height + button_spacing) * idx
                    ),
                    text=item,
                    **common_kwargs
                )
            )

        common_kwargs['frameSize'][1] = 0.15
        buttons.insert(0,
            DirectButton(
                pos=(-0.95, 0, 0.375),
                text=add_power_item,
                **common_kwargs
            )
        )

        return buttons

    def rebuild_stats(self, monsterdata):
        self._stats_header['text'] = monsterdata["name"]
        self._stats_golem['text'] = (
            f'Hit Points: {monsterdata["hit_points"]}\t'
            f'Physical Attack: {monsterdata["physical_attack"]}\n'
            f'Movement: {monsterdata["movement"]}\t'
            f'Magical Attack: {monsterdata["magical_attack"]}\n'
            'Power:\n'
            f'\t{monsterdata["power_spent"]}/{monsterdata["power_available"]}'
        )

        form = monsterdata['form']
        self._stats_form['text'] = (
            f'Form: {form["name"]}\n'
            f'  Abilities:'
        )

        weapon = monsterdata['weapon']
        self._stats_weapon['text'] = (
            f'Weapon:\n'
            f'  Abilities:\t\tStats:\n'
            f'  \t\t  Power: {weapon["damage"]}\n'
            f'  \t\t  Type: {weapon["type"]}\n'
            f'  \t\t  Range Min: {weapon["range_min"]}\n'
            f'  \t\t  Range Max: {weapon["range_max"]}\n'
        )
