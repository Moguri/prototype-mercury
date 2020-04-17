# pylint: disable=protected-access
import pytest

def test_level(monster):
    '''Monster level is one plus the sum of the gained job levels'''
    assert monster.level == 1

    monster._monsterdata.jp_totals = {
        'foo': 100,
        'bar': 0
    }
    assert monster.level == 2

    monster._monsterdata.jp_totals = {
        'foo': 200,
        'bar': 100
    }
    assert monster.level == 4

def test_stats(monster):
    stats = {
        'hit_points': 130,
        "physical_attack": 130,
        "magical_attack": 120,
        "defense": 120,
        "evasion": 130,
        "accuracy": 120,
    }

    monster.add_jp('bobcatshark', monster.JP_PER_LEVEL)
    for key, value in stats.items():
        assert getattr(monster, key) == value

def test_tags(monster):
    assert 'breed_bobcatshark' in monster.tags
    monster.add_jp('bobcatshark', 1)
    assert 'job_bobcatshark_1' in monster.tags

def test_job_assignment(monster, gdb):
    job = gdb['jobs']['bruiser']

    assert not monster.can_use_job(job)
    with pytest.raises(RuntimeError, match=r'tag requirements unsatisfied'):
        monster.job = job

    monster.add_jp('squire', monster.JP_PER_LEVEL)
    assert monster.can_use_job(job)
    monster.job = job
