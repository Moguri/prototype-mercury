# pylint: disable=protected-access

def test_level(monster):
    '''Monster level is the sum of the job levels'''
    monster._monsterdata.job_levels = {
        'foo': 2,
        'bar': 1
    }

    assert monster.level == 3

def test_stats(monster):
    stats = {
        'hit_points': 100,
        "physical_attack": 100,
        "magical_attack": 100,
        "defense": 100,
        "evasion": 100,
        "accuracy": 100,
    }

    for key, value in stats.items():
        assert getattr(monster, key) == value
