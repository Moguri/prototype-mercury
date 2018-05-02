import gamedb


gamedb.VALIDATE_SCHEMA = True


def test_load():
    gamedb.GameDB.get_instance()
