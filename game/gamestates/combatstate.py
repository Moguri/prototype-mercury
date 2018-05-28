import math
import random

from direct.interval import IntervalGlobal as intervals
import panda3d.core as p3d

import ai
from combatant import Combatant
import effects
import gamedb

from .gamestate import GameState


class CameraController():
    def __init__(self, camera, combatants):
        self.camera = camera
        self.combatants = combatants
        self._old_cam_parent = camera.get_parent()
        self.widget = camera.get_parent().attach_new_node('camera_widget')

        self.camera.reparent_to(self.widget)
        self.widget.set_p(-20.0)
        self.widget.set_z(1.0)
        self.camera.set_pos(self.widget, p3d.LVecBase3(0.0, -7.5, 0.0))

    def cleanup(self):
        self.camera.reparent_to(self._old_cam_parent)
        self.widget.remove_node()

    def update(self):
        positions = [combatant.path.get_x() for combatant in self.combatants]

        target_pos = math.fsum(positions) / len(positions)
        current_pos = self.widget.get_x()
        movement = 0.035 * (target_pos - current_pos)
        new_pos = current_pos + movement
        self.widget.set_x(new_pos)

        distance = max(positions) - min(positions)
        offset_factor = (distance - 2.0) / 8.0
        target_offset = offset_factor * 10.0 + 7.5
        current_offset = -self.camera.get_y(self.widget)
        offset_delta = 0.01 * (target_offset - current_offset)
        offset_vector = p3d.LVecBase3(0.0, -(current_offset + offset_delta), 0.0)
        self.camera.set_pos(self.widget, offset_vector)


class CombatState(GameState):
    COMBAT_MAX_TIME = 60
    ARENA_EDGE = 9
    KNOCKBACK_DISTANCE = 3
    RANGE_WIDTH = 2.0

    def __init__(self):
        super().__init__()
        gdb = gamedb.get_instance()

        self.range_index = 0
        self.combat_over = 0

        self.arena_model = base.loader.load_model('arena.bam')
        self.arena_model.reparent_to(self.root_node)

        if 'breeds' in base.blackboard:
            breeds = [gdb['breeds'][i] for i in base.blackboard['breeds']]
        else:
            print('No breeds in blackboard, using random')
            available_breeds = list(gdb['breeds'].values())
            breeds = [
                random.choice(available_breeds),
                random.choice(available_breeds),
            ]

        self.combatants = [
            Combatant(
                breeds[0],
                self.arena_model,
                ['p1-ability{}'.format(i) for i in range(4)]
            ),
            Combatant(
                breeds[1],
                self.arena_model,
                ['p2-ability{}'.format(i) for i in range(4)]
            ),
        ]
        self.combatants[0].path.set_x(-1.0)
        self.combatants[0].path.set_h(-90)
        self.combatants[0].target = self.combatants[1]
        self.combatants[1].path.set_x(1.0)
        self.combatants[1].path.set_h(90)
        self.combatants[1].target = self.combatants[0]

        # Combatant 0 inputs
        for idx, inp in enumerate(self.combatants[0].ability_inputs):
            self.accept(inp, self.use_ability, [self.combatants[0], idx])
        self.accept('p1-move-left', self.move_combatant, [self.combatants[0], -1])
        self.accept('p1-move-right', self.move_combatant, [self.combatants[0], 1])
        self.accept(
            'p1-knockback',
            self.use_knockback,
            [self.combatants[0], self.combatants[1], 1]
        )

        # Combatant 1 inputs
        for idx, inp in enumerate(self.combatants[1].ability_inputs):
            self.accept(inp, self.use_ability, [self.combatants[1], idx])
        self.accept('p2-move-left', self.move_combatant, [self.combatants[1], -1])
        self.accept('p2-move-right', self.move_combatant, [self.combatants[1], 1])
        self.accept(
            'p2-knockback',
            self.use_knockback,
            [self.combatants[1], self.combatants[0], -1]
        )

        self.combat_timer = p3d.ClockObject()

        # AI controller for player two
        if base.blackboard['use_ai']:
            self.ai_controller = ai.Controller(self.combatants[1])
        else:
            self.ai_controller = None

        # UI
        self.load_ui('combat')
        self.wintext = p3d.TextNode('win text')
        self.wintext.set_align(p3d.TextNode.ACenter)
        self.wintextnp = base.aspect2d.attach_new_node(self.wintext)
        self.wintextnp.set_pos(0, 0, 0)
        self.wintextnp.set_scale(0.25)
        self.wintextnp.hide()

        self.cam_controller = CameraController(base.camera, self.combatants)

    def cleanup(self):
        super().cleanup()
        self.cam_controller.cleanup()
        self.cam_controller = None
        self.wintextnp.remove_node()

        base.taskMgr.remove('Combat State')

    def move_combatant(self, combatant, delta, free_move=False, override_lock=False):
        if combatant.lock_controls and not override_lock:
            return

        delta *= self.RANGE_WIDTH

        index = self.combatants.index(combatant)

        new_positions = [combatant.path.get_x() for combatant in self.combatants]
        new_position = max(-self.ARENA_EDGE, min(new_positions[index] + delta, self.ARENA_EDGE))

        if new_positions[index] == new_position:
            return

        new_positions[index] = new_position
        distance = max(new_positions) - min(new_positions)

        if distance > 8 or distance < 2:
            return

        move_cost = 0 if free_move else combatant.move_cost
        if combatant.current_ap < move_cost:
            return

        combatant.current_ap -= move_cost
        combatant.path.set_x(new_position)
        self.range_index = int((distance - 2) // 2)

    def use_knockback(self, combatant, target, direction):
        if combatant.lock_controls:
            return

        if combatant.range_index != 0:
            return

        self.move_combatant(target, direction*self.KNOCKBACK_DISTANCE, free_move=True)

    def use_ability(self, combatant, index):
        if combatant.lock_controls:
            return

        if len(combatant.abilities) <= index:
            return

        ability = combatant.abilities[index]
        if not combatant.ability_is_usable(ability):
            return

        combatant.current_ap -= ability.cost

        sequence = effects.sequence_from_ability(self.root_node, combatant, ability, self)

        def unlock_combatant():
            combatant.lock_controls = 0
        def cleanup():
            combatant.target.lock_controls = 0
            combatant.path.loop(combatant.get_anim('idle'))
        sequence.extend(intervals.Sequence(
            intervals.Func(cleanup),
            intervals.Wait(0.25),
            intervals.Func(unlock_combatant)
        ))
        for cbt in self.combatants:
            cbt.lock_controls = 1
        sequence.start()

    def update(self, dt):
        self.cam_controller.update()

        if self.combat_over:
            return

        combat_time = self.combat_timer.get_real_time()
        time_remaining = self.COMBAT_MAX_TIME - combat_time

        for combatant in self.combatants:
            combatant.update(dt, self.range_index)

        if self.ai_controller:
            self.ai_controller.update(dt)

        end_combat = (
            time_remaining <= 0 or
            self.combatants[0].current_hp <= 0 or
            self.combatants[1].current_hp <= 0
        )
        if end_combat:
            for combatant in self.combatants:
                combatant.lock_controls = 1
            self.combat_over = 1

            # cleanup UI a little
            if time_remaining < 0:
                time_remaining = 0
            for combatant in self.combatants:
                if combatant.current_hp < 0:
                    combatant.current_hp = 0

            # display the results
            winstring = 'Combatant %s Wins!'
            if self.combatants[0].current_hp > self.combatants[1].current_hp:
                winstring = winstring % 'One'
            elif self.combatants[1].current_hp > self.combatants[0].current_hp:
                winstring = winstring % 'Two'
            else:
                winstring = 'Draw!'
                self.wintextnp.set_scale(0.5)
            self.wintext.set_text(winstring)
            self.wintextnp.show()

            # wait for user input to transition
            def reset():
                base.change_state('CharacterSelection')

            self.accept('p1-accept', reset)
            self.accept('p2-accept', reset)

        self.update_ui({
            'timer': math.floor(time_remaining),
            'range': self.range_index,
            'player_monster': self.combatants[0].get_state(),
            'opponent_monster': self.combatants[1].get_state(),
        })
