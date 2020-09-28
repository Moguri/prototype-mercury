# pylint: disable=protected-access
import pytest

def test_level(monster):
    '''Monster level is one plus the sum of the gained job levels'''
    jp_per_level = monster.JP_PER_LEVEL
    assert monster.level == 1

    monster.add_jp('foo', jp_per_level)
    assert monster.level == 2

    monster.add_jp('foo', jp_per_level)
    monster.add_jp('bar', jp_per_level)
    assert monster.level == 4

def test_tags(monster):
    assert 'form_bobcatshark' in monster.tags
    monster.add_jp('bobcatshark', 1)
    assert 'job_bobcatshark_1' in monster.tags

    monster.add_jp('bobcatshark', monster.JP_PER_LEVEL)
    assert 'job_bobcatshark_1' in monster.tags
    assert 'job_bobcatshark_2' in monster.tags

def test_job_assignment(monster, gdb):
    job = gdb['jobs']['skirmisher']

    assert not monster.can_use_job(job)
    with pytest.raises(RuntimeError, match=r'tag requirements unsatisfied'):
        monster.job = job

    monster.add_jp('brawler', monster.JP_PER_LEVEL * 2)
    assert monster.can_use_job(job)
    monster.job = job

def test_stats(monster):
    assert monster.hit_points == 11
    assert monster.physical_attack == 7
    assert monster.magical_attack == 6
    assert monster.movement == 6

def test_stat_upgrade(monster):
    monster.upgrade_stat('hp')
    assert monster.upgrades_for_stat('hp') == 1
    assert monster.hp == 12
    assert monster.jp_unspent[monster.job.id] == 0

def test_gen_random(monster):
    mon = monster.gen_random('test', 1)
    assert mon
    assert mon.level == 1
    # assert mon.abilities

    mon = monster.gen_random('test', 5)
    assert mon
    assert mon.level == 5
