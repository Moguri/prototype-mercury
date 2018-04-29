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


def calculate_hit_chance(_combatant, _target, _ability):
    return 100


def calculate_strength(combatant, _target, ability):
    ab_str = ability.damage_rank * 10
    cmb_str = (
        combatant.physical_attack
        if ability.type == 'physical'
        else combatant.magical_attack
    )

    return ab_str * cmb_str


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
