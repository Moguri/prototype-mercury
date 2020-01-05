from game import effects

def test_smoke():
    #pylint: disable=protected-access
    effects._test()


def test_calc_hit_mod():
    assert effects.calculate_hit_mod(300, 250) == 5
    assert effects.calculate_hit_mod(100, 250) == -12.5
    assert effects.calculate_hit_mod(1000, 0) == 40


def test_calc_str_fac():
    assert effects.calculate_strength_factor(400, 100) == 1.5
    assert effects.calculate_strength_factor(50, 150) == 0.8


def test_calc_def_fac():
    assert effects.calculate_defense_factor(100) == 0.9
    assert effects.calculate_defense_factor(0) == 1
    assert effects.calculate_defense_factor(1000) == 0
    assert effects.calculate_defense_factor(475) == 0.525
