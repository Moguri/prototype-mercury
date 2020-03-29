# pylint: disable=protected-access

def test_level(monster):
    '''Monster level is the sum of the job levels'''
    monster._monsterdata.job_levels = {
        'foo': 2,
        'bar': 1
    }

    assert monster.level == 3
