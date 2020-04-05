import random

import panda3d.core as p3d
from direct.interval import IntervalGlobal as intervals


BP_HITMOD = [
    [100, 10],
    [200, 20],
    [300, 30],
    [400, 40],
]

BP_STRFAC = [
    [100, 400],
    [200, 800],
    [300, 1200],
    [400, 1600],
]

def _bpsum(diff, bps):
    tot = 0

    for break_point in bps:
        tot += max(min(diff, break_point[0]) / break_point[1], 0)
        diff -= break_point[0]

    return tot


def calculate_hit_mod(self_acc, target_eva):
    diff = abs(self_acc - target_eva)
    mod = _bpsum(diff, BP_HITMOD)

    return mod if self_acc > target_eva else -mod


def calculate_hit_chance(combatant, target, ability):
    base_chance = 40 + ability.hit_rank * 10

    return base_chance + calculate_hit_mod(combatant.accuracy, target.evasion)


def calculate_strength_factor(self_stat, opp_stat):
    diff = abs(self_stat - opp_stat)
    factor = 1 + _bpsum(diff, BP_STRFAC)

    return factor if self_stat > opp_stat else 1 / factor


def calculate_defense_factor(defense):
    return 1 - (defense / 1000)


def calculate_strength(combatant, target, ability):
    self_stat = (
        combatant.physical_attack
        if ability.type == 'physical'
        else combatant.magical_attack
    )
    opp_stat = (
        target.physical_attack
        if ability.type == 'physical'
        else target.magical_attack
    )
    base_str = (ability.damage_rank * 0.25 - 0.2) * self_stat
    str_factor = calculate_strength_factor(self_stat, opp_stat)
    def_factor = calculate_defense_factor(target.defense)

    return round(base_str * str_factor * def_factor)

class SequenceBuilder:
    ALLOWED_EFFECTS = [
        'change_stat',
        'show_result',
        'play_animation',
        'move_to_range',
        'move_to_start',

        'template_simple',
    ]

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

    #
    # Basic Effects
    #
    def change_stat(self, target, parameters):
        stat = parameters['stat']
        def func():
            if self.is_hit:
                setattr(target, stat, getattr(target, stat) - self.strength)
        return intervals.Func(func)


    def show_result(self, target, _parameters):
        textnode = p3d.TextNode('effect result')
        textnode.set_align(p3d.TextNode.ACenter)
        textnode.set_text(str(self.strength) if self.is_hit else "Miss")

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


    def play_animation(self, target, parameters):
        return target.actor_interval(parameters['animation_name'])

    def move_to_range(self, target, parameters):
        target_range = parameters['range']
        hit_required = parameters.get('is_hit_dependent', False)

        if hit_required and not self.is_hit:
            return intervals.Sequence()

        def func():
            self.combat.move_combatant_to_range(
                target,
                target.target,
                target_range
            )

        return intervals.Func(func)

    def move_to_start(self, target, _parameters):
        target_pos = self.initial_position
        def func():
            self.combat.move_combatant_to_tile(
                target,
                target_pos
            )
        return intervals.Func(func)

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

        sequence.extend(intervals.Sequence(
            self.play_animation(self.combatant, parameters),
            self.show_result(target, parameters),
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
