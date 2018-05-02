import random

import panda3d.core as p3d
from direct.interval import IntervalGlobal as intervals


def change_stat(_combatant, target, hit, strength, parameters, _rendernp):
    stat = parameters['stat']
    def func():
        if hit:
            setattr(target, stat, getattr(target, stat) - strength)
    return intervals.Func(func)


def show_result(_combatant, target, hit, strength, _parameters, rendernp):
    textnode = p3d.TextNode('effect result')
    textnode.set_align(p3d.TextNode.ACenter)
    textnode.set_text(str(strength) if hit else "Miss")

    textnp = rendernp.attach_new_node(textnode)
    textnp.set_pos(target.path, 0, 0, 2)
    textnp.set_billboard_point_eye()
    textnp.set_bin("fixed", 0)
    textnp.set_depth_test(False)
    textnp.set_depth_write(False)
    textnp.set_scale(0.5)
    textnp.hide()

    return intervals.Sequence(
        intervals.Func(textnp.show),
        intervals.LerpPosInterval(
            textnp,
            0.5,
            textnp.get_pos() + p3d.LVector3(0, 0, 0.5)
        ),
        intervals.Func(textnp.remove_node),
    )


def play_animation(combatant, target, _hit, _strength, parameters, _rendernp):
    return target.path.actor_interval(
        combatant.get_anim(parameters['animation_name'])
    )


_EFFECT_MAP = {
    'change_stat': change_stat,
    'play_animation': play_animation,
    'show_result': show_result,
}


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

    for breakpoint in bps:
        tot += max(min(diff, breakpoint[0]) / breakpoint[1], 0)
        diff -= breakpoint[0]

    return tot


def calculate_hit_mod(self_acc, target_eva):
    diff = abs(self_acc - target_eva)
    mod = _bpsum(diff, BP_HITMOD)

    return mod if self_acc > target_eva else -mod


def calculate_hit_chance(combatant, target, ability):
    base_chance = 45 + ability.hit_rank * 10

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
    base_str = (ability.damage_rank * 0.35 - 0.2) * self_stat
    str_factor = calculate_strength_factor(self_stat, opp_stat)
    def_factor = calculate_defense_factor(target.defense)

    return round(base_str * str_factor * def_factor)


def sequence_from_ability(rendernp, combatant, ability):
    sequence = intervals.Sequence()

    hit_chance = calculate_hit_chance(combatant, combatant.target, ability)
    roll = random.randrange(0, 99)
    hit = hit_chance > roll
    #print(hit, hit_chance, die)
    strength = calculate_strength(combatant, combatant.target, ability)

    for effect in ability.effects:
        target = effect.get('target', 'other')
        if target == 'self':
            target = combatant
        elif target == 'other':
            target = combatant.target
        else:
            raise RuntimeError("Unkown effect target: {}".format(target))

        parameters = effect.get('parameters', {})
        etype = effect['type']

        if etype not in _EFFECT_MAP:
            raise RuntimeError("Unknown effect type: {}".format(etype))

        sequence.append(_EFFECT_MAP[etype](combatant, target, hit, strength, parameters, rendernp))

    return sequence


def _test():
    import pprint
    from gamedb import GameDB
    from combatant import Combatant

    gdb = GameDB.get_instance()

    breeds = list(gdb['breeds'].values())
    cmb = Combatant(breeds[0], None, [])
    cmb.target = cmb

    for ability in gdb['abilities'].values():
        print(ability.name)
        pprint.pprint(ability.effects)

        print(sequence_from_ability(p3d.NodePath(), cmb, ability))


if __name__ == '__main__':
    _test()
