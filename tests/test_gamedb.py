from game import gamedb


gamedb.VALIDATE_SCHEMA = True


def test_load():
    gamedb.get_instance()
