import random

import panda3d.core as p3d
from direct.interval import IntervalGlobal as intervals


def calculate_hit_chance(_combatant, _target, ability):
    return ability.hit_chance


def calculate_strength(combatant, _target, ability):
    attack_stat = (
        combatant.physical_attack
        if ability.type == 'physical'
        else combatant.magical_attack
    )

    return round(attack_stat * ability.power)

class SequenceBuilder:
    ALLOWED_EFFECTS = [
        'change_stat',
        'play_animation',
        'move_to_range',
        'move_to_start',

        'template_simple',
    ]

    CHANGE_STATE_PREFIX = {
        'current_hp': 'HP: ',
        'current_mp': 'MP: ',
        'physical_attack': 'PA: ',
        'magical_attack': 'MA: ',
        'movement': 'MOV: ',
    }

    def __init__(self, rendernp, combatant, ability, combat):
        self.rendernp = rendernp
        self.combatant = combatant
        self.ability = ability
        self.combat = combat

        hit_chance = calculate_hit_chance(combatant, combatant.target, ability)
        roll = random.randrange(0, 99)
        self.is_hit = hit_chance > roll
        #print(hit, hit_chance, die)
        self.strength = calculate_strength(combatant, combatant.target, ability)

        self.sequence = intervals.Sequence()

        self.initial_self_position = combatant.tile_position
        self.initial_other_position = combatant.target.tile_position
        self.initial_position = None

        for effect in ability.effects:
            self.sequence.extend(self.parse_effect(effect))
        self.sequence.append(
            intervals.Func(combatant.play_anim, 'idle', loop=True),
        )

    def parse_effect(self, effect):
        sequence = intervals.Sequence()
        target = effect.get('target', 'other')
        if target == 'self':
            target = self.combatant
            self.initial_position = self.initial_self_position
        elif target == 'other':
            target = self.combatant.target
            self.initial_position = self.initial_other_position
        else:
            raise RuntimeError("Unkown effect target: {}".format(target))

        parameters = effect.get('parameters', {})
        etype = effect['type']

        if etype not in self.ALLOWED_EFFECTS:
            raise RuntimeError("Unknown effect type: {}".format(etype))

        sequence.append(getattr(self, etype)(target, parameters))

        return sequence

    def as_sequence(self):
        return self.sequence

    def show_result(self, target, value):
        textnode = p3d.TextNode('effect result')
        textnode.set_align(p3d.TextNode.ACenter)
        textnode.set_text(value)

        textnp = self.rendernp.attach_new_node(textnode)
        textnp.set_pos(target.as_nodepath, 0, 0, 2)
        textnp.set_billboard_point_eye()
        textnp.set_bin("fixed", 0)
        textnp.set_depth_test(False)
        textnp.set_depth_write(False)
        textnp.set_shader_auto(True)
        textnp.hide()

        def func():
            intervals.Sequence(
                intervals.Func(textnp.show),
                intervals.LerpPosInterval(
                    textnp,
                    1.0,
                    textnp.get_pos() + p3d.LVector3(0, 0, 0.5)
                ),
                intervals.Func(textnp.remove_node),
            ).start()

        return intervals.Func(func)

    #
    # Basic Effects
    #
    def change_stat(self, target, parameters):
        stat = parameters['stat']
        seq = intervals.Sequence()
        strength = self.strength
        if stat not in ('current_hp', 'current_mp'):
            strength = max(round(abs(strength) * 0.1), 1)
            if self.strength < 0:
                strength *= -1
        if parameters.get('show_result', True):
            if self.is_hit:
                result = self.CHANGE_STATE_PREFIX.get(stat, '') + f'{strength * -1:+}'
            else:
                result = 'Miss'
            seq.append(self.show_result(target, result))
        def func():
            if self.is_hit:
                setattr(target, stat, getattr(target, stat) - strength)
        seq.append(intervals.Func(func))
        return seq

    def play_animation(self, target, parameters):
        anims = parameters.get('animation_name', [])
        if isinstance(anims, str):
            anims = [anims]
        anims.insert(0, self.ability.id)
        anims.append('attack')
        return target.actor_interval(anims)

    def move_to_range(self, target, parameters):
        target_range = parameters['range']
        hit_required = parameters.get('is_hit_dependent', False)

        if hit_required and not self.is_hit:
            return intervals.Sequence()

        seq = self.combat.move_combatant_to_range(
            target,
            target.target,
            target_range
        )
        return seq

    def move_to_start(self, target, _parameters):
        target_pos = self.initial_position
        return self.combat.move_combatant_to_tile(
            target,
            target_pos
        )

    #
    # Template Effects
    #
    def template_simple(self, target, parameters):
        sequence = intervals.Sequence()
        if 'stat' not in parameters:
            parameters['stat'] = 'current_hp'
        if 'start_range' in parameters:
            parameters['range'] = parameters['start_range']
            sequence.append(self.move_to_range(self.combatant, parameters))
        if 'animation_name' not in parameters and self.ability.type == 'magical':
            parameters['animation_name'] = 'magic'

        sequence.extend(intervals.Sequence(
            self.play_animation(self.combatant, parameters),
            self.change_stat(target, parameters),
        ))

        if 'start_range' in parameters:
            if 'end_range' in parameters:
                parameters['range_index'] = parameters['end_range']
            else:
                parameters['range_index'] = -1
            sequence.append(self.move_to_range(self.combatant, parameters))

        return sequence


def sequence_from_ability(rendernp, combatant, ability, combat):
    return SequenceBuilder(rendernp, combatant, ability, combat).as_sequence()
