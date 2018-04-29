from direct.interval import IntervalGlobal as intervals


def change_stat(combatant, target, parameters):
    strength = (
        parameters.get('physical_coef', 0) * combatant.physical_attack +
        parameters.get('magical_coef', 0) * combatant.magical_attack +
        parameters.get('base_coef', 0)
    )
    stat = parameters['stat']
    def func():
        setattr(target, stat, getattr(target, stat) - strength)
    return intervals.Func(func)


def play_animation(combatant, target, parameters):
    return target.path.actor_interval(
        combatant.get_anim(parameters['animation_name'])
    )


_EFFECT_MAP = {
    'change_stat': change_stat,
    'play_animation': play_animation,
}


def sequence_from_effects(combatant, effects):
    sequence = intervals.Sequence()

    for effect in effects:
        target = effect.get('target', 'other')
        if target == 'self':
            target = combatant
        elif target == 'other':
            target = combatant.target
        else:
            raise RuntimeError("Unkown effect target: {}".format(target))
        parameters = effect['parameters']
        etype = effect['type']

        if etype not in _EFFECT_MAP:
            raise RuntimeError("Unknown effect type: {}".format(etype))

        sequence.append(_EFFECT_MAP[etype](combatant, target, parameters))

    return sequence


if __name__ == '__main__':
    import pprint
    from gamedb import GameDB
    from combatant import Combatant

    GDB = GameDB.get_instance()

    CMB = Combatant(None, [], [])
    CMB.target = CMB

    for ability in GDB['abilities'].values():
        print(ability.name)
        pprint.pprint(ability.effects)

        print(sequence_from_effects(CMB, ability.effects))
