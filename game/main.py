import json
import math
import os
import random
import sys

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.interval import IntervalGlobal as intervals
from direct.actor.Actor import Actor
import panda3d.core as p3d

import cefpanda
import blenderpanda
import eventmapper
import effects
from combatant import Combatant
from gamedb import GameDB


if hasattr(sys, 'frozen'):
    APP_ROOT_DIR = os.path.dirname(sys.executable)
else:
    APP_ROOT_DIR = p3d.Filename.from_os_specific(os.path.abspath(os.path.dirname(__file__)))
if not APP_ROOT_DIR:
    print('empty app_root_dir')
    sys.exit()

# Load config files before ShowBase is initialized
CONFIG_DIR = p3d.Filename(APP_ROOT_DIR, 'config')
p3d.load_prc_file(p3d.Filename(CONFIG_DIR, 'game.prc'))
p3d.load_prc_file(p3d.Filename(CONFIG_DIR, 'inputs.prc'))
p3d.load_prc_file(p3d.Filename(CONFIG_DIR, 'user.prc'))


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





class GameState(DirectObject):
    def __init__(self):
        super().__init__()
        self.root_node = p3d.NodePath('State Root')
        self.root_node.reparent_to(base.render)

    def cleanup(self):
        self.ignoreAll()
        self.root_node.remove_node()
        self.root_node = None

    def update(self, dt):
        pass


class CharacterSelectionState(GameState):
    class PlayerInfo:
        def __init__(self, name, max_selection):
            self.name = name
            self.max_selection = max_selection
            self.selection = 0
            self.selection_locked = False

        def get_state(self):
            return {
                'name': self.name,
                'sel_idx': self.selection,
                'is_locked': self.selection_locked,
            }

        def _step_selection(self, step):
            if not self.selection_locked:
                self.selection = max(0, min(self.selection + step, self.max_selection))

        def increment_selection(self):
            self._step_selection(1)

        def decrement_selection(self):
            self._step_selection(-1)

        def lock_selection(self):
            self.selection_locked = True

        def unlock_selection(self):
            self.selection_locked = False

    class BreedDisplay:
        def __init__(self, left, right, top, bottom):
            self.dispregion = base.win.make_display_region(
                left, right, top, bottom
            )

            self.root = p3d.NodePath('breed-display-root')

            self.cam = p3d.Camera('breed-display-cam')
            self.cam.get_lens().set_aspect_ratio(
                self.dispregion.get_pixel_width() / self.dispregion.get_pixel_height()
            )
            self.camnp = self.root.attach_new_node(self.cam)
            self.dispregion.set_camera(self.camnp)

            self.camnp.set_pos(0, -3, 3)
            self.camnp.look_at(p3d.LVector3(0, 0, 1))

            self.light = p3d.DirectionalLight('dlight')
            self.lightnp = self.root.attach_new_node(self.light)
            self.lightnp.set_pos(2, -4, 4)
            self.lightnp.look_at(p3d.LVector3(0, 0, 0))
            self.root.set_light(self.lightnp)

            self._last_breed = None
            self.model = Actor()
            self.model.reparent_to(self.root)

        def set_breed(self, breed):
            if self._last_breed == breed.id:
                return
            self._last_breed = breed.id

            self.model.cleanup()
            self.model.remove_node()

            model = base.loader.load_model('{}.bam'.format(breed.bam_file))
            self.model = Actor(model.find('**/{}'.format(breed.root_node)))
            self.model.set_h(180)
            self.model.loop(breed.anim_map['idle'])
            self.model.reparent_to(self.root)

        def cleanup(self):
            base.win.remove_display_region(self.dispregion)

    def __init__(self):
        super().__init__()
        gdb = GameDB.get_instance()

        max_selection = len(gdb['breeds']) - 1
        self.players = [
            self.PlayerInfo('Player One', max_selection),
            self.PlayerInfo('Player Two', max_selection),
        ]

        for idx, player in enumerate(self.players):
            self.accept('p{}-move-down'.format(idx + 1), player.increment_selection)
            self.accept('p{}-move-up'.format(idx + 1), player.decrement_selection)
            self.accept('p{}-accept'.format(idx + 1), player.lock_selection)
            self.accept('p{}-reject'.format(idx + 1), player.unlock_selection)

        self.breeds_list = sorted(gdb['breeds'].values(), key=lambda x: x.name)
        base.load_ui('char_sel')

        self.breed_displays = [
            self.BreedDisplay(0.25, 0.5, 0.33, 1),
            self.BreedDisplay(0.5, 0.75, 0.33, 1),
        ]

        # only send breeds once
        state = {
            'breeds': [i.to_dict() for i in self.breeds_list],
        }
        base.ui.execute_js('update_state({})'.format(json.dumps(state)), onload=True)

    def cleanup(self):
        super().cleanup()
        for disp in self.breed_displays:
            disp.cleanup()

    def update(self, dt):
        gdb = GameDB.get_instance()
        breed_ids = [
            self.breeds_list[player.selection].id
            for player in self.players
        ]

        if all((player.selection_locked for player in self.players)):
            base.blackboard['breeds'] = breed_ids
            base.change_state(CombatState)

        for idx, breedid in enumerate(breed_ids):
            self.breed_displays[idx].set_breed(gdb['breeds'][breedid])

        # update ui
        state = {
            'players': [i.get_state() for i in self.players],
        }
        base.ui.execute_js('update_state({})'.format(json.dumps(state)), onload=True)


class CombatState(GameState):
    COMBAT_MAX_TIME = 60
    ARENA_EDGE = 9
    KNOCKBACK_DISTANCE = 3
    RANGE_WIDTH = 2.0

    def __init__(self):
        super().__init__()
        gdb = GameDB.get_instance()

        self.lock_controls = 0
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

        # UI
        base.load_ui('combat')
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
        if self.lock_controls and not override_lock:
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
        if self.lock_controls:
            return

        if combatant.range_index != 0:
            return

        self.move_combatant(target, direction*self.KNOCKBACK_DISTANCE, free_move=True)

    def use_ability(self, combatant, index):
        if self.lock_controls:
            return

        if len(combatant.abilities)  <= index:
            return

        ability = combatant.abilities[index]
        if not combatant.ability_is_usable(ability):
            return

        combatant.current_ap -= ability.cost

        sequence = effects.sequence_from_ability(self.root_node, combatant, ability, self)

        def cleanup():
            self.lock_controls = 0
            combatant.path.loop(combatant.get_anim('idle'))
        sequence.append(intervals.Func(cleanup))
        self.lock_controls = 1
        sequence.start()

    def update(self, dt):
        self.cam_controller.update()

        if self.combat_over:
            return

        combat_time = self.combat_timer.get_real_time()
        time_remaining = self.COMBAT_MAX_TIME - combat_time

        for combatant in self.combatants:
            combatant.update(dt, self.range_index)

        end_combat = (
            time_remaining <= 0 or
            self.combatants[0].current_hp <= 0 or
            self.combatants[1].current_hp <= 0
        )
        if end_combat:
            self.lock_controls = 1
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
                if p3d.ConfigVariableBool('mercury-skip-to-combat', 'False').get_value():
                    next_state = CombatState
                else:
                    next_state = CharacterSelectionState
                base.change_state(next_state)

            self.accept('p1-accept', reset)
            self.accept('p2-accept', reset)

        state = {
            'timer': math.floor(time_remaining),
            'range': self.range_index,
            'player_monster': self.combatants[0].get_state(),
            'opponent_monster': self.combatants[1].get_state(),
        }

        base.ui.execute_js('update_state({})'.format(json.dumps(state)), onload=True)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        GameDB.get_instance()

        self.win.set_close_request_event('escape')
        self.accept('escape', sys.exit)

        self.disable_mouse()
        self.render.set_shader_auto()
        self.render.set_antialias(p3d.AntialiasAttrib.MAuto)

        self.blackboard = {}

        self.event_mapper = eventmapper.EventMapper()

        # UI
        self.ui = cefpanda.CEFPanda()

        # Game states
        if p3d.ConfigVariableBool('mercury-skip-to-combat', 'False').get_value():
            self.current_state = CombatState()
        else:
            self.current_state = CharacterSelectionState()
        def update_gamestate(task):
            self.current_state.update(p3d.ClockObject.get_global_clock().get_dt())
            return task.cont
        self.taskMgr.add(update_gamestate, 'GameState')

    def change_state(self, next_state):
        self.current_state.cleanup()
        self.current_state = next_state()

    def load_ui(self, uiname):
        self.ui.load(os.path.join(APP_ROOT_DIR, 'ui', '{}.html'.format(uiname)))



APP = GameApp()
APP.run()

# Hack to fix PyLint errors
#pylint: disable=invalid-name
base = APP
