from direct.interval import IntervalGlobal as intervals


def change_stat(combatant, target, parameters):
    strength = (
        parameters.get('physical_coef', 0) * combatant.physical_attack +
        parameters.get('magical_coef', 0) * combatant.magical_attack +
        parameters.get('base_coef', 0)
    )
    stat = parameters['stat']
    def change_stat():
        setattr(target, stat, getattr(target, stat) - strength)
    return intervals.Func(change_stat)


_effect_map = {
    'change_stat': change_stat,
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

        if etype not in _effect_map:
            raise RuntimeError("Unknown effect type: {}".format(etype))

        sequence.append(_effect_map[etype](combatant, target, parameters))

    return sequence


if __name__ == '__main__':
    import pprint
    from gamedb import GameDB
    from combatant import Combatant

    gdb = GameDB.get_instance()

    combatant = Combatant(None, [])
    combatant.target = combatant

    for ability in gdb['abilities'].values():
        print(ability.name)
        pprint.pprint(ability.effects)

        print(sequence_from_effects(combatant, ability.effects))
