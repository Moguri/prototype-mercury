import itertools
import math
import random

from direct.interval import IntervalGlobal as intervals
import panda3d.core as p3d

from .. import effects
from .. import gamedb
from ..monster import Monster
from ..combatant import Combatant

from .gamestate import GameState
from .commonlighting import CommonLighting

class CombatState(GameState):
    SELECTED_COLOR = (3, 0, 0, 1)
    RANGE_COLOR = (0, 0, 3, 1)

    def __init__(self):
        super().__init__()

        gdb = gamedb.get_instance()

        self._input_state = None

        # Arena
        arena_tiles = base.loader.load_model('arena_tiles.bam')
        self.tile_model = arena_tiles.find('**/ArenaTile')

        self.arena = self.root_node.attach_new_node('Arena')
        self.tilenps = []

        self.xsize = 5
        self.ysize = 5
        arena_center = (
            self.xsize // 2,
            self.ysize // 2
        )
        for xtile in range(self.xsize):
            self.tilenps.append([])
            for ytile in range(self.ysize):
                xpos, ypos, _ = self.tile_coord_to_world(xtile, ytile)
                zpos = (random.random() - 0.5) / 10.0 - 1.0
                tilenp = self.arena.attach_new_node(f'arenatile-{xtile}-{ytile}')
                tilenp.set_pos((xpos, ypos, zpos))
                self.tile_model.instance_to(tilenp)
                self.tilenps[-1].append(tilenp)
        self.arena.flatten_medium()
        self.selected_tile = (4, 3)
        self.range_tiles = []

        # Combatants
        available_monsters = [i for i in list(gdb['monsters'].values()) if i.id != 'player_monster']
        monsters = [
            random.choice(available_monsters),
            random.choice(available_monsters),
        ]
        if 'monsters' in base.blackboard:
            for idx, monster in enumerate(base.blackboard['monsters']):
                monsters[idx] = gdb['monsters'][monster]

        self.player_combatants = [
            Combatant(
                Monster(monsters[0]),
                self.root_node,
                []
            )
        ]
        self.enemy_combatants = [
            Combatant(
                Monster(monsters[1]),
                self.root_node,
                []
            ),
        ]
        self.move_combatant_to_tile(
            self.player_combatants[0],
            (4, 3)
        )
        self.move_combatant_to_tile(
            self.enemy_combatants[0],
            (4, 4)
        )
        self.selected_combatant = self.player_combatants[0]
        self.selected_ability = None

        # Setup Lighting
        arena_world_center = self.tile_coord_to_world(*arena_center)
        CommonLighting(self.root_node, arena_world_center)

        # Setup Camera
        base.camera.set_pos(-10, -10, 10)
        base.camera.look_at(self.tile_coord_to_world(*arena_center))

        # Setup UI
        def reject_cb():
            if self.input_state == 'ACTION':
                self.input_state = 'SELECT'
        self.menu_helper.reject_cb = reject_cb
        self.load_ui('combat')

        # Set initial input state
        self.input_state = 'SELECT'

    @property
    def combatants(self):
        return (
            i
            for i in itertools.chain(self.player_combatants, self.enemy_combatants)
            if not i.is_dead
        )

    @property
    def input_state(self):
        return self._input_state

    @input_state.setter
    def input_state(self, value):
        self.ignore_all()
        self.menu_helper.show = False
        self.menu_helper.lock = True
        self.menu_helper.selection_idx = 0
        self.display_message('')
        def show_menu(menu):
            self.menu_helper.set_menu(menu)
            self.menu_helper.lock = False
            self.menu_helper.show = True
        def setup_selection(accept_cb, reject_cb=None):
            self.accept('move-up', self.move_selection, [(0, 1)])
            self.accept('move-left', self.move_selection, [(-1, 0)])
            self.accept('move-down', self.move_selection, [(0, -1)])
            self.accept('move-right', self.move_selection, [(1, 0)])
            self.accept('move-up-repeat', self.move_selection, [(0, 1)])
            self.accept('move-left-repeat', self.move_selection, [(-1, 0)])
            self.accept('move-down-repeat', self.move_selection, [(0, -1)])
            self.accept('move-right-repeat', self.move_selection, [(1, 0)])
            self.accept('accept', accept_cb)
            if reject_cb is not None:
                self.accept('reject', reject_cb)

        if value == 'SELECT':
            def accept_selection():
                selection = self.combatant_in_tile(self.selected_tile)
                if selection:
                    self.selected_combatant = selection
                    self.input_state = 'ACTION'
            setup_selection(accept_selection)
            self.display_message('Select a combatant')
        elif value == 'ACTION':
            def set_input_state(state):
                self.input_state = state
            def use_ability(ability):
                self.input_state = 'TARGET'
                self.selected_ability = ability
            self.menu_helper.menus['action'] = [
                ('Move', set_input_state, ['MOVE']),
            ] + [
                (ability.name, use_ability, [ability])
                for ability in self.selected_combatant.abilities
            ]
            show_menu('action')
            self.display_message('Select an action')
        elif value == 'MOVE':
            def accept_move():
                selection = self.combatant_in_tile(self.selected_tile)
                if selection is None:
                    self.move_combatant_to_tile(
                        self.selected_combatant,
                        self.selected_tile
                    )
                    self.input_state = 'SELECT'

            def reject_move():
                self.selected_tile = self.selected_combatant.tile_position
                self.input_state = 'ACTION'

            setup_selection(accept_move, reject_move)
            self.display_message('Select new location')
        elif value == 'TARGET':
            def accept_target():
                selection = self.combatant_in_tile(self.selected_tile)
                in_range = self.tile_in_range(
                    self.selected_tile,
                    self.selected_combatant.tile_position,
                    self.selected_ability.range_min,
                    self.selected_ability.range_max
                )
                if selection is not None and in_range:
                    self.display_message(
                        f'{self.selected_combatant.name} is using {self.selected_ability.name} '
                        f'on {selection.name}'
                    )
                    self.selected_combatant.target = selection
                    selection.target = self.selected_combatant
                    def cleanup():
                        self.selected_ability = None
                        self.selected_tile = self.selected_combatant.tile_position
                        for combatant in (self.selected_combatant, selection):
                            if combatant.is_dead:
                                combatant.play_anim('death')
                        self.input_state = 'SELECT'
                    sequence = effects.sequence_from_ability(
                        self.root_node,
                        self.selected_combatant,
                        self.selected_ability,
                        self
                    )
                    sequence.extend(intervals.Sequence(
                        intervals.Func(cleanup)
                    ))
                    sequence.start()

            def reject_target():
                self.selected_tile = self.selected_combatant.tile_position
                self.input_state = 'ACTION'

            setup_selection(accept_target, reject_target)
            self.display_message('Select a target')
        elif value == 'END':
            if not self.get_remaining_enemy_combatants():
                self.display_message('Victory!')
            else:
                self.display_message('Defeat.')

            self.accept('accept', base.change_to_previous_state)
            self.accept('reject', base.change_to_previous_state)
        else:
            raise RuntimeError(f'Unknown state {value}')

        self._input_state = value

    def vec_to_tile_coord(self, vec):
        return tuple(int(i) for i in vec)

    def tile_coord_in_bounds(self, tile_pos):
        return bool(self.xsize > tile_pos[0] >= 0 and self.ysize > tile_pos[1] >= 0)

    def tile_coord_to_world(self, xtile, ytile):
        return p3d.LVector3(xtile * 2, ytile * 2, 0)

    def tilenp_to_coord(self, tilenp):
        return tuple([int(i) for i in tilenp.name.split('-')[-2:]])

    def combatant_in_tile(self, tile_pos):
        combatants = [
            i
            for i in self.combatants
            if i.tile_position == tile_pos
        ]

        return combatants[0] if combatants else None

    def move_combatant_to_tile(self, combatant, tile_pos):
        if not self.tile_coord_in_bounds(tile_pos):
            return False

        combatant.tile_position = tile_pos
        combatant.path.set_pos(self.tile_coord_to_world(*tile_pos))

        return True

    def tile_get_facing_to(self, from_tile, to_tile):
        posa = p3d.LVector2(from_tile)
        posb = p3d.LVector2(to_tile)

        direction = posb - posa
        direction.normalize()
        direction.x = round(direction.x)
        direction.y = round(direction.y)

        facing = [int(i) for i in direction]

        # Special cases
        if abs(facing[0]) == 1 and abs(facing[1]) == 1:
            facing[1] = 0

        return tuple(facing)

    def move_combatant_to_range(self, combatant, other, target_range):
        distance = self.tile_distance(
            combatant.tile_position,
            other.tile_position
        )
        if distance == target_range:
            return

        direction = p3d.LVector2(self.tile_get_facing_to(
            combatant.tile_position,
            other.tile_position
        ))
        other_pos = p3d.LVector2(other.tile_position)
        new_pos = self.vec_to_tile_coord(-direction * target_range + other_pos)
        self.move_combatant_to_tile(combatant, new_pos)

    def move_selection(self, vector):
        selection = self.vec_to_tile_coord(p3d.LVector2(self.selected_tile) + p3d.LVector2(vector))

        if self.tile_coord_in_bounds(selection):
            self.selected_tile = selection

    def tile_distance(self, tilea, tileb):
        distvec = p3d.LVector2(tilea) - p3d.LVector2(tileb)
        return abs(distvec.x) + abs(distvec.y)

    def tile_in_range(self, tile_coord, start, min_range, max_range):
        tiledist = self.tile_distance(start, tile_coord)
        return bool(min_range <= tiledist <= max_range)

    def find_tiles_in_range(self, start, min_range, max_range):
        tiles = []
        for tile_coord in (self.tilenp_to_coord(i) for i in itertools.chain(*self.tilenps)):
            if self.tile_in_range(tile_coord, start, min_range, max_range):
                tiles.append(tile_coord)
        return tiles

    def display_message(self, msg):
        self.update_ui({
            'message': msg,
        })

    def get_remaining_player_combatants(self):
        return [
            i
            for i in self.player_combatants
            if not i.is_dead
        ]

    def get_remaining_enemy_combatants(self):
        return [
            i
            for i in self.enemy_combatants
            if not i.is_dead
        ]

    def update(self, dt):
        super().update(dt)

        # Check for end condition
        if not self.get_remaining_player_combatants() or not self.get_remaining_enemy_combatants():
            self.input_state = 'END'

        # Update combatant facing
        if self.input_state in ('MOVE', 'TARGET'):
            facing = self.tile_get_facing_to(
                self.selected_combatant.tile_position,
                self.selected_tile
            )
            if sum(facing) != 0:
                self.selected_combatant.path.set_h(
                    math.degrees(math.atan2(facing[1], facing[0])) - 90
                )

        # Update tile color tints
        if self.input_state == 'ACTION':
            if self.menu_helper.selection_idx != 0:
                self.selected_ability = self.selected_combatant.abilities[
                    self.menu_helper.selection_idx - 1
                ]
            else:
                self.selected_ability = None

        if self.selected_ability is not None:
            self.range_tiles = self.find_tiles_in_range(
                self.selected_combatant.tile_position,
                self.selected_ability.range_min,
                self.selected_ability.range_max
            )
        else:
            self.range_tiles = []

        for tilenp in itertools.chain(*self.tilenps):
            tile_coord = self.tilenp_to_coord(tilenp)
            if tile_coord == self.selected_tile:
                color = self.SELECTED_COLOR
            elif tile_coord in self.range_tiles:
                color = self.RANGE_COLOR
            else:
                color = (1, 1, 1, 1)
            tilenp.set_color(color)
