# pylint: disable=protected-access

from game.monster import Monster

def test_tags(monster):
    assert 'form_bobcatshark' in monster.tags

def test_passive_upgrade(monster):
    prevhp = monster.hit_points
    monster.abilities_learned_form.append('hp_up')
    assert monster.hit_points > prevhp

def test_gen_random():
    mon = Monster.gen_random('test', 1)
    assert mon
