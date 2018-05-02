import random

from direct.interval import IntervalGlobal as intervals


def change_stat(_combatant, target, hit, strength, parameters):
    stat = parameters['stat']
    def func():
        if hit:
            setattr(target, stat, getattr(target, stat) - strength)
    return intervals.Func(func)


def play_animation(combatant, target, _hit, _strength, parameters):
    return target.path.actor_interval(
        combatant.get_anim(parameters['animation_name'])
    )


_EFFECT_MAP = {
    'change_stat': change_stat,
    'play_animation': play_animation,
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


def sequence_from_ability(combatant, ability):
    sequence = intervals.Sequence()

    for effect in ability.effects:
        target = effect.get('target', 'other')
        if target == 'self':
            target = combatant
        elif target == 'other':
            target = combatant.target
        else:
            raise RuntimeError("Unkown effect target: {}".format(target))
        hit = calculate_hit_chance(combatant, target, ability) > random.randrange(0, 99)
        strength = calculate_strength(combatant, target, ability)
        parameters = effect['parameters']
        etype = effect['type']

        if etype not in _EFFECT_MAP:
            raise RuntimeError("Unknown effect type: {}".format(etype))

        sequence.append(_EFFECT_MAP[etype](combatant, target, hit, strength, parameters))

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

        print(sequence_from_ability(cmb, ability))


if __name__ == '__main__':
    _test()
