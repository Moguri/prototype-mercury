import itertools
import math
import random

from direct.interval import IntervalGlobal as intervals
import panda3d.core as p3d

from ..monster import Monster
from ..combatant import Combatant
from ..commonlighting import CommonLighting
from .. import bgnode

from .gamestate import GameState

class Arena:
    def __init__(self, parent_node, sizex, sizey):
        self.root_node = parent_node.attach_new_node('Arena')
        arena_tiles = base.loader.load_model('models/arena_tiles.bam')
        self.tile_model = arena_tiles.find('**/ArenaTile')

        self.tilenps = []

        self.sizex = sizex
        self.sizey = sizey
        self.center = (
            self.sizex // 2,
            self.sizey // 2
        )
        for xtile in range(self.sizex):
            self.tilenps.append([])
            for ytile in range(self.sizey):
                xpos, ypos, _ = self.tile_coord_to_world((xtile, ytile))
                zpos = (random.random() - 0.5) / 10.0 - 1.0
                tilenp = self.root_node.attach_new_node(f'arenatile-{xtile}-{ytile}')
                tilenp.set_pos((xpos, ypos, zpos))
                self.tile_model.instance_to(tilenp)
                self.tilenps[-1].append(tilenp)
        self.root_node.flatten_medium()

    def vec_to_tile_coord(self, vec):
        return tuple(int(i) for i in vec)

    def tile_coord_in_bounds(self, tile_pos):
        return bool(self.sizex > tile_pos[0] >= 0 and self.sizey > tile_pos[1] >= 0)

    def tile_coord_to_world(self, tile_pos):
        xtile, ytile = tile_pos
        return p3d.LVector3(xtile * 2, ytile * 2, 0)

    def tilenp_to_coord(self, tilenp):
        return tuple([int(i) for i in tilenp.name.split('-')[-2:]])

    def tile_distance(self, tilea, tileb):
        distvec = p3d.LVector2(tilea) - p3d.LVector2(tileb)
        return int(abs(distvec.x) + abs(distvec.y))

    def tile_in_range(self, tile_coord, start, min_range, max_range):
        tiledist = self.tile_distance(start, tile_coord)
        return bool(min_range <= tiledist <= max_range)

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

    def find_tiles_in_range(self, start, min_range, max_range):
        tiles = []
        for tile_coord in (self.tilenp_to_coord(i) for i in itertools.chain(*self.tilenps)):
            if self.tile_in_range(tile_coord, start, min_range, max_range):
                tiles.append(tile_coord)
        return tiles

    def color_tiles(self, color, tiles=None):
        for tilenp in itertools.chain(*self.tilenps):
            tile_coord = self.tilenp_to_coord(tilenp)
            if tiles is None or tile_coord in tiles:
                tilenp.set_color(color)


class AiController():
    def __init__(self, arena, controller, effects_root):
        self.arena = arena
        self.controller = controller
        self.effects_root = effects_root
        self.targets = {}

    def update_combatant(self, combatant, enemy_combatants):
        sequence = intervals.Sequence()

        # Find a target
        target = self.targets.get(combatant, None)
        if target is None or target.is_dead():
            target = random.choice(enemy_combatants)
        for enemy in enemy_combatants:
            dist_to_closest = self.arena.tile_distance(
                combatant.tile_position,
                target.tile_position
            )
            dist_to_current = self.arena.tile_distance(
                combatant.tile_position,
                enemy.tile_position
            )
            if dist_to_current < dist_to_closest:
                target = enemy

        # Pick an ability
        available_abilities = [
            ability
            for ability in combatant.abilities
            if combatant.can_use_ability(ability)
        ]

        if not available_abilities:
            return sequence

        ability = random.choice(available_abilities)

        # Update facing
        sequence.append(
            intervals.Func(
                self.controller.face_combatant_at_tile,
                combatant,
                target.tile_position
            )
        )

        # Find a tile to move to
        tiles = self.arena.find_tiles_in_range(
            combatant.tile_position,
            0,
            combatant.movement
        )
        tiles = [tile for tile in tiles if self.controller.combatant_in_tile(tile) is None]
        target_tile = None
        dist_to_target = self.arena.tile_distance(
            combatant.tile_position,
            target.tile_position
        )
        range_min, range_max = self.controller.get_ability_range(combatant, ability)
        for tile in tiles:
            tile_dist = self.arena.tile_distance(
                tile,
                target.tile_position
            )
            if range_min <= tile_dist <= range_max:
                target_tile = tile
                dist_to_target = tile_dist
                break
            elif tile_dist < dist_to_target:
                target_tile = tile
                dist_to_target = tile_dist

        if target_tile and combatant.can_move():
            self.controller.selected_tile = target_tile
            sequence.extend([
                self.controller.move_combatant_to_tile(combatant, target_tile),
            ])

        # Update facing
        sequence.append(
            intervals.Func(
                self.controller.face_combatant_at_tile,
                combatant,
                target.tile_position
            )
        )

        # Use an ability if able
        if range_min <= dist_to_target <= range_max:
            sequence.extend([
                intervals.WaitInterval(0.25),
                combatant.use_ability(
                    ability,
                    target,
                    self.controller,
                    self.effects_root
                ),
                intervals.WaitInterval(1),
            ])

        return sequence


class CombatState(GameState):
    SELECTED_COLOR = (3, 0, 0, 1)
    RANGE_COLOR = (0, 0, 3, 1)

    def __init__(self):
        super().__init__()

        # Background Image
        bgnode.generate(self.root_node, 'arena')
        bgnode.generate(self.root_node, 'arena', True)

        # Background Music
        self.play_bg_music('the_last_encounter')

        # Arena
        self.arena = Arena(self.root_node, 10, 10)
        self.selected_tile = (0, 0)
        self.range_tiles = []

        self.player = base.blackboard['player']

        # Player Combatants
        self.player_combatants = [
            Combatant(mon, self.root_node) for mon in self.player.monsters
        ]
        random_placement = p3d.ConfigVariableBool(
            'mercury-random-combat-placement',
            True
        ).get_value()
        possible_positions = [
            (x, y)
            for x in range(2)
            for y in range(self.arena.sizey - 1)
        ]
        if random_placement:
            placements = random.sample(possible_positions, len(self.player_combatants))
        else:
            placements = possible_positions
        for combatant, placement in zip(self.player_combatants, placements):
            self.move_combatant_to_tile(
                combatant,
                placement,
                True
            )
            combatant.set_h(90)

        # Enemy Combatants
        default_combat_type = p3d.ConfigVariableString('mercury-default-combat-type', 'skirmish')
        self.combat_type = base.blackboard.get('combat_type', default_combat_type)
        if self.combat_type == 'tournament':
            num_enemies = {
                1: 3,
                2: 5,
                3: 8
            }.get(self.player.rank, 8)
        else:
            num_enemies = len(self.player_combatants)
        self.enemy_combatants = [
            Combatant(
                Monster.gen_random(f'combatant{i}', 1),
                self.root_node
            )
            for i in range(num_enemies)
        ]
        possible_positions = [
            (x, y)
            for x in range(self.arena.sizex - 1, self.arena.sizex - 3, -1)
            for y in range(self.arena.sizey - 1)
        ]
        placements = random.sample(possible_positions, len(self.enemy_combatants))
        for combatant, placement in zip(self.enemy_combatants, placements):
            self.move_combatant_to_tile(
                combatant,
                placement,
                True
            )
            combatant.set_h(-90)

        # Setup Lighting
        arena_world_center = self.arena.tile_coord_to_world(self.arena.center)
        CommonLighting(self.root_node, arena_world_center)

        # Setup Camera
        base.camera.set_pos(-15, -15, 15)
        lookat_offset = p3d.LVector3(-3, -3, 0)
        base.camera.look_at(self.arena.tile_coord_to_world(self.arena.center) + lookat_offset)

        # Setup UI
        self.load_ui('combat')

        # Setup AI
        self.aicontroller = AiController(self.arena, self, self.root_node)

        # Set initial input state
        self.input_state = 'END_TURN'

    @property
    def combatants(self):
        return (
            i
            for i in itertools.chain(self.player_combatants, self.enemy_combatants)
            if not i.is_dead
        )

    def setup_selection(self, accept_cb, reject_cb=None):
        def accept_cb_wrap():
            self.menu_helper.sfx_accept.play()
            accept_cb()
        def reject_cb_wrap():
            self.menu_helper.sfx_reject.play()
            if reject_cb is not None:
                reject_cb()

        def move_selection(vector):
            selection = self.arena.vec_to_tile_coord(
                p3d.LVector2(self.selected_tile) + p3d.LVector2(vector)
            )
            self.menu_helper.sfx_select.play()

            if self.arena.tile_coord_in_bounds(selection):
                self.selected_tile = selection
        self.accept('move-up', move_selection, [(0, 1)])
        self.accept('move-left', move_selection, [(-1, 0)])
        self.accept('move-down', move_selection, [(0, -1)])
        self.accept('move-right', move_selection, [(1, 0)])
        self.accept('move-up-repeat', move_selection, [(0, 1)])
        self.accept('move-left-repeat', move_selection, [(-1, 0)])
        self.accept('move-down-repeat', move_selection, [(0, -1)])
        self.accept('move-right-repeat', move_selection, [(1, 0)])
        self.accept('accept', accept_cb_wrap)
        self.accept('reject', reject_cb_wrap)

    def enter_state(self):
        super().enter_state()

        self.display_message(None)
        self.range_tiles = []

        # Kill all enemies cheat
        # def kill_all():
        #     print('Setting enemy health to 0')
        #     for combatant in self.enemy_combatants:
        #         combatant.current_hp = 0
        # self.accept('k', kill_all)

    def enter_select(self, combatant):
        def accept_selection():
            selection = self.combatant_in_tile(self.selected_tile)
            if selection and selection == combatant:
                self.set_input_state('ACTION', combatant)
        self.setup_selection(accept_selection)
        self.display_message('Select a combatant')

    def enter_action(self, combatant):
        if combatant.ability_used and not combatant.can_move():
            # Out of actions, auto end turn
            self.set_input_state('END_TURN')
            return

        def use_ability(ability):
            if combatant.can_use_ability(ability):
                self.set_input_state('TARGET', combatant, ability)
        def end_combat():
            self.set_input_state('END_COMBAT', forfeit=True)

        menu_items = []
        if combatant.can_move():
            menu_items.append(('Move', self.set_input_state, ['MOVE', combatant]))

        if not combatant.ability_used:
            menu_items += [
                (f'{ability.name}', use_ability, [ability])
                for ability in combatant.abilities
            ]

        menu_items.extend([
            ('End Turn', self.set_input_state, ['END_TURN']),
            ('End Combat', end_combat, [])
        ])

        self.menu_helper.set_menu(combatant.name, menu_items)

        def update_ability(menu_item):
            self.range_tiles = []
            item_name = menu_item[0]
            if item_name == 'Move':
                self.range_tiles = self.arena.find_tiles_in_range(
                    combatant.tile_position,
                    0,
                    combatant.move_current
                )
            elif item_name not in ('Rest', 'End Turn', 'End Combat'):
                ability = menu_item[2][0]
                self.range_tiles = self.arena.find_tiles_in_range(
                    combatant.tile_position,
                    *self.get_ability_range(combatant, ability)
                )
        update_ability(self.menu_helper.current_selection)
        self.menu_helper.selection_change_cb = update_ability
        def action_reject():
            self.set_input_state('SELECT', combatant)
        self.menu_helper.reject_cb = action_reject

    def enter_move(self, combatant):
        self.range_tiles = self.arena.find_tiles_in_range(
            combatant.tile_position,
            0,
            combatant.move_current
        )
        def accept_move():
            selection = self.combatant_in_tile(self.selected_tile)
            if selection == combatant:
                selection = None
            in_range = self.arena.tile_in_range(
                self.selected_tile,
                combatant.tile_position,
                0,
                combatant.move_current
            )
            if selection is None and in_range:
                dist = self.arena.tile_distance(
                    combatant.tile_position,
                    self.selected_tile
                )
                combatant.move_current -= dist
                intervals.Sequence(
                    self.move_combatant_to_tile(
                        combatant,
                        self.selected_tile
                    ),
                    intervals.Func(self.set_input_state, 'ACTION', combatant)
                ).start()

        def reject_move():
            self.selected_tile = combatant.tile_position
            self.set_input_state('ACTION', combatant)

        self.setup_selection(accept_move, reject_move)
        self.display_message('Select new location')

    def update_move(self, _dt, combatant):
        self.face_combatant_at_tile(
            combatant,
            self.selected_tile
        )

    def enter_target(self, combatant, ability):
        self.range_tiles = self.arena.find_tiles_in_range(
            combatant.tile_position,
            *self.get_ability_range(combatant, ability)
        )
        def accept_target():
            selection = self.combatant_in_tile(self.selected_tile)
            in_range = self.arena.tile_in_range(
                self.selected_tile,
                combatant.tile_position,
                *self.get_ability_range(combatant, ability)
            )
            if selection is not None and in_range:
                sequence = combatant.use_ability(
                    ability,
                    selection,
                    self,
                    self.root_node
                )
                def cleanup():
                    self.selected_tile = combatant.tile_position
                    if self.input_state != 'END_COMBAT':
                        self.set_input_state('END_TURN')
                sequence.append(
                    intervals.Func(cleanup)
                )
                sequence.start()

        def reject_target():
            self.selected_tile = combatant.tile_position
            self.set_input_state('ACTION', combatant)

        self.setup_selection(accept_target, reject_target)
        self.display_message('Select a target')

    def update_target(self, _dt, combatant, _ability):
        self.face_combatant_at_tile(
            combatant,
            self.selected_tile
        )

    def enter_end_turn(self):
        combatants_by_ct = sorted(
            list(self.combatants),
            reverse=True,
            key=lambda x: x.current_ct
        )
        next_combatant = combatants_by_ct[0]
        next_combatant.move_current = next_combatant.move_max
        next_combatant.ability_used = False
        ctdiff = 100 - next_combatant.current_ct
        if ctdiff > 0:
            for combatant in self.combatants:
                combatant.current_ct += ctdiff
        next_combatant.current_ct = 0
        self.selected_tile = next_combatant.tile_position

        if next_combatant in self.player_combatants:
            self.set_input_state('ACTION', next_combatant)
        else:
            sequence = self.aicontroller.update_combatant(
                next_combatant,
                self.get_remaining_player_combatants()
            )
            def cleanup():
                if self.input_state != 'END_COMBAT':
                    self.input_state = 'END_TURN'
            sequence.extend([
                intervals.Func(cleanup),
            ])
            sequence.start()

    def enter_end_combat(self, forfeit=False):
        results = []
        isvictory = not self.get_remaining_enemy_combatants()
        if forfeit:
            self.display_message('Match was forfeited')
        elif isvictory:
            self.display_message('Victory!')
            if self.combat_type == 'tournament':
                self.player.rank += 1
                results += [
                    f'Advanced to Rank {self.player.rank}'
                ]
        else:
            self.display_message('Defeat.')

        self.update_ui({'results': results})
        self.accept('accept', base.change_to_previous_state)
        self.accept('reject', base.change_to_previous_state)

    def combatant_in_tile(self, tile_pos):
        combatants = [
            i
            for i in self.combatants
            if i.tile_position == tile_pos
        ]

        return combatants[0] if combatants else None

    def move_combatant_to_tile(self, combatant, tile_pos, immediate=False):
        if immediate:
            duration = 0
        else:
            duration = self.arena.tile_distance(combatant.tile_position, tile_pos) * 0.2
        combatant.tile_position = tile_pos
        newpos = self.arena.tile_coord_to_world(tile_pos)
        sequence = intervals.Sequence(
            intervals.Func(combatant.play_anim, 'walk', loop=True),
            intervals.LerpPosInterval(
                combatant.as_nodepath,
                duration,
                newpos
            ),
            intervals.Func(combatant.play_anim, 'idle', loop=True)
        )
        if immediate:
            sequence.start()
        return sequence

    def find_tile_at_range(self, combatant, other, target_range):
        distance = self.arena.tile_distance(
            combatant.tile_position,
            other.tile_position
        )

        inc = 1 if target_range < distance else -1

        new_pos = combatant.tile_position
        for target in range(target_range, distance, inc):
            direction = p3d.LVector2(self.arena.tile_get_facing_to(
                combatant.tile_position,
                other.tile_position
            ))
            other_pos = p3d.LVector2(other.tile_position)
            pos = self.arena.vec_to_tile_coord(-direction * target + other_pos)
            pos_legal = (
                self.arena.tile_coord_in_bounds(pos)
                and not self.combatant_in_tile(pos)
            )
            if pos_legal:
                new_pos = pos
                break

        return new_pos

    def move_combatant_to_range(self, combatant, other, target_range):
        new_pos = self.find_tile_at_range(combatant, other, target_range)
        return self.move_combatant_to_tile(combatant, new_pos)

    def face_combatant_at_tile(self, combatant, tile):
        facing = self.arena.tile_get_facing_to(
            combatant.tile_position,
            tile
        )
        self.change_combatant_facing(
            combatant,
            facing
        )

    def change_combatant_facing(self, combatant, facing):
        if sum(facing) != 0:
            combatant.set_h(
                math.degrees(math.atan2(facing[1], facing[0])) + 90
            )

    def get_ability_range(self, combatant, ability):
        if ability.range_min == 'weapon':
            range_min = combatant.weapon.range_min
        else:
            range_min = ability.range_min

        if ability.range_max == 'weapon':
            range_max = combatant.weapon.range_max
        else:
            range_max = ability.range_max

        return (range_min, range_max)

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

    def combat_over(self):
        return (
            not self.get_remaining_player_combatants() or
            not self.get_remaining_enemy_combatants()
        )

    def update(self, dt):
        super().update(dt)

        # Check for end condition
        if self.combat_over() and self.input_state != 'END_COMBAT':
            self.input_state = 'END_COMBAT'

        # Update tile color tints
        self.arena.color_tiles((1, 1, 1, 1))
        self.arena.color_tiles(self.RANGE_COLOR, self.range_tiles)
        self.arena.color_tiles(self.SELECTED_COLOR, [self.selected_tile])

        # Update stat display
        combatant_at_cursor = self.combatant_in_tile(self.selected_tile)
        if combatant_at_cursor and self.input_state != 'END_COMBAT':
            self.update_ui({'monster': combatant_at_cursor.get_state()})
        else:
            self.update_ui({'monster': {}})
