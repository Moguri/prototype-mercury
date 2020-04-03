# pylint: disable=protected-access
import pytest

def test_level(monster):
    '''Monster level is the sum of the job levels'''
    monster._monsterdata.job_levels = {
        'foo': 2,
        'bar': 1
    }

    assert monster.level == 3

def test_stats(monster):
    stats = {
        'hit_points': 115,
        "physical_attack": 115,
        "magical_attack": 110,
        "defense": 110,
        "evasion": 115,
        "accuracy": 110,
    }

    for key, value in stats.items():
        assert getattr(monster, key) == value

def test_tags(monster):
    assert 'breed_bobcatshark' in monster.tags
    assert 'job_bobcatshark_1' in monster.tags

def test_job_assignment(monster, gdb):
    job = gdb['jobs']['bruiser']

    assert not monster.can_use_job(job)
    with pytest.raises(RuntimeError, match=r'tag requirements unsatisfied'):
        monster.job = job

    monster.job_levels['squire'] = 2
    assert monster.can_use_job(job)
    monster.job = job
    assert monster.job_levels[job.id] == 1
