# pylint: disable=unused-argument
import pprint

import pytest

from game import gamedb
from game import effects

@pytest.mark.parametrize("ability", gamedb.get_instance()['abilities'].values())
def test_smoke(app, combatant, empty_nodepath, ability, combat):
    combatant.target = combatant
    print(ability.name)
    pprint.pprint(ability.effects)
    effects.sequence_from_ability(empty_nodepath, combatant, ability, combat)


def test_accuracy(combatant, basic_attack):
    assert effects.calculate_hit_chance(combatant, combatant, basic_attack) == 100


def test_strength(combatant, basic_attack):
    combatant.weapon = None
    assert effects.calculate_strength(combatant, basic_attack) == 6

    combatant.weapon = 'mace'
    assert effects.calculate_strength(combatant, basic_attack) == 7
