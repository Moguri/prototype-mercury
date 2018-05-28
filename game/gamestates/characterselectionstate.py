from direct.actor.Actor import Actor
import panda3d.core as p3d

from gamedb import GameDB

from .gamestate import GameState

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
        self.load_ui('char_sel')

        self.breed_displays = [
            self.BreedDisplay(0.25, 0.5, 0.33, 1),
            self.BreedDisplay(0.5, 0.75, 0.33, 1),
        ]

        # only send breeds once
        self.update_ui({
            'breeds': [i.to_dict() for i in self.breeds_list],
        })

    def cleanup(self):
        super().cleanup()
        for disp in self.breed_displays:
            disp.cleanup()

    def update(self, _dt):
        gdb = GameDB.get_instance()
        breed_ids = [
            self.breeds_list[player.selection].id
            for player in self.players
        ]

        if all((player.selection_locked for player in self.players)):
            base.blackboard['breeds'] = breed_ids
            base.change_state('Combat')

        for idx, breedid in enumerate(breed_ids):
            self.breed_displays[idx].set_breed(gdb['breeds'][breedid])

        # update ui
        self.update_ui({
            'players': [i.get_state() for i in self.players],
        })
