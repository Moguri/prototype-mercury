import itertools
import math
import random

from direct.interval import IntervalGlobal as intervals
import panda3d.core as p3d

from .. import effects
from .. import gamedb
from ..monster import Monster
from ..combatant import Combatant
from ..commonlighting import CommonLighting

from .gamestate import GameState

class CombatState(GameState):
    SELECTED_COLOR = (3, 0, 0, 1)
    RANGE_COLOR = (0, 0, 3, 1)

    def __init__(self):
        super().__init__()

        gdb = gamedb.get_instance()

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
        self.selected_tile = (0, 0)
        self.range_tiles = []

        self.player = base.blackboard['player']

        # Combatants
        available_monsters = [
            i
            for i in list(gdb['monsters'].values())
            if i.id not in ('player_monster', 'bobcatshark')
        ]

        self.player_combatants = [
            Combatant(mon, self.root_node) for mon in self.player.monsters
        ]
        for idx, combatant in enumerate(self.player_combatants):
            self.move_combatant_to_tile(
                combatant,
                (0, idx)
            )
            combatant.path.set_h(-90)

        self.enemy_combatants = [
            Combatant(
                Monster(random.choice(available_monsters)),
                self.root_node
            ),
        ]
        for idx, combatant in enumerate(self.enemy_combatants):
            self.move_combatant_to_tile(
                combatant,
                (4, idx)
            )
            combatant.path.set_h(90)
        self.selected_ability = None
        self.current_combatant = None

        # Setup Lighting
        arena_world_center = self.tile_coord_to_world(*arena_center)
        CommonLighting(self.root_node, arena_world_center)

        # Setup Camera
        base.camera.set_pos(-10, -10, 10)
        base.camera.look_at(self.tile_coord_to_world(*arena_center))

        # Setup UI
        self.load_ui('combat')

        # Set initial input state
        self.input_state = 'END_TURN'

    @property
    def combatants(self):
        return (
            i
            for i in itertools.chain(self.player_combatants, self.enemy_combatants)
            if not i.is_dead
        )

    def set_input_state(self, next_state):
        self.display_message('')
        super().set_input_state(next_state)

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

        if next_state == 'SELECT':
            def accept_selection():
                selection = self.combatant_in_tile(self.selected_tile)
                if selection and selection == self.current_combatant:
                    self.input_state = 'ACTION'
            setup_selection(accept_selection)
            self.display_message('Select a combatant')
        elif next_state == 'ACTION':
            def use_ability(ability):
                self.input_state = 'TARGET'
                self.selected_ability = ability
            self.menu_helper.set_menu(self.current_combatant.name, [
                ('Move', self.set_input_state, ['MOVE']),
            ] + [
                (ability.name, use_ability, [ability])
                for ability in self.current_combatant.abilities
            ])
            def update_ability(idx):
                if idx == 0:
                    self.selected_ability = None
                else:
                    self.selected_ability = self.current_combatant.abilities[idx - 1]
            self.menu_helper.selection_change_cb = update_ability
            def action_reject():
                self.input_state = 'SELECT'
            self.menu_helper.reject_cb = action_reject
        elif next_state == 'MOVE':
            def accept_move():
                selection = self.combatant_in_tile(self.selected_tile)
                in_range = self.tile_in_range(
                    self.selected_tile,
                    self.current_combatant.tile_position,
                    0,
                    self.current_combatant.movement
                )
                if selection is None and in_range:
                    self.move_combatant_to_tile(
                        self.current_combatant,
                        self.selected_tile
                    )
                    self.input_state = 'SELECT'

            def reject_move():
                self.selected_tile = self.current_combatant.tile_position
                self.input_state = 'ACTION'

            setup_selection(accept_move, reject_move)
            self.display_message('Select new location')
        elif next_state == 'TARGET':
            def accept_target():
                selection = self.combatant_in_tile(self.selected_tile)
                in_range = self.tile_in_range(
                    self.selected_tile,
                    self.current_combatant.tile_position,
                    self.selected_ability.range_min,
                    self.selected_ability.range_max
                )
                if selection is not None and in_range:
                    self.display_message(
                        f'{self.current_combatant.name} is using {self.selected_ability.name} '
                        f'on {selection.name}'
                    )
                    self.current_combatant.target = selection
                    selection.target = self.current_combatant
                    sequence = effects.sequence_from_ability(
                        self.root_node,
                        self.current_combatant,
                        self.selected_ability,
                        self
                    )
                    def cleanup():
                        for combatant in (self.current_combatant, selection):
                            if combatant.is_dead:
                                combatant.play_anim('death')
                        self.current_combatant.current_ct = 0
                        self.input_state = 'END_TURN'
                    sequence.extend(intervals.Sequence(
                        intervals.Func(cleanup)
                    ))
                    sequence.start()

            def reject_target():
                self.selected_tile = self.current_combatant.tile_position
                self.input_state = 'ACTION'

            setup_selection(accept_target, reject_target)
            self.display_message('Select a target')
        elif next_state == 'END_TURN':
            self.selected_ability = None
            combatants_by_ct = sorted(
                list(self.combatants),
                reverse=True,
                key=lambda x: x.current_ct
            )
            self.current_combatant = combatants_by_ct[0]
            ctdiff = 100 - self.current_combatant.current_ct
            if ctdiff > 0:
                for combatant in self.combatants:
                    combatant.current_ct += ctdiff
                    print(f'{combatant.name}: {combatant.current_ct} CT')
            self.selected_tile = self.current_combatant.tile_position
            self.input_state = 'ACTION'
        elif next_state == 'END_COMBAT':
            if not self.get_remaining_enemy_combatants():
                self.display_message('Victory!')
            else:
                self.display_message('Defeat.')

            self.accept('accept', base.change_to_previous_state)
            self.accept('reject', base.change_to_previous_state)
        else:
            raise RuntimeError(f'Unknown state {next_state}')

        self._input_state = next_state

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
            self.input_state = 'END_COMBAT'

        # Update combatant facing
        if self.input_state in ('MOVE', 'TARGET'):
            facing = self.tile_get_facing_to(
                self.current_combatant.tile_position,
                self.selected_tile
            )
            if sum(facing) != 0:
                self.current_combatant.path.set_h(
                    math.degrees(math.atan2(facing[1], facing[0])) - 90
                )

        # Update tile color tints
        if self.input_state == 'MOVE':
            self.range_tiles = self.find_tiles_in_range(
                self.current_combatant.tile_position,
                0,
                self.current_combatant.movement
            )
        elif self.selected_ability is not None:
            self.range_tiles = self.find_tiles_in_range(
                self.current_combatant.tile_position,
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

        combatant_at_cursor = self.combatant_in_tile(self.selected_tile)
        if combatant_at_cursor:
            self.update_ui({'monster': combatant_at_cursor.get_state()})
        else:
            self.update_ui({'monster': {}})
