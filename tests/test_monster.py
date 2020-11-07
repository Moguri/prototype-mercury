# pylint: disable=protected-access

from game.monster import Monster

def test_tags(monster):
    assert 'form_bobcatshark' in monster.tags

# def test_stats(monster):
#     assert monster.hit_points == 11
#     assert monster.physical_attack == 7
#     assert monster.magical_attack == 6
#     assert monster.movement == 6

def test_gen_random():
    mon = Monster.gen_random('test', 1)
    assert mon
