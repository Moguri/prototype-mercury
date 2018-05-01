import gamedb


gamedb.VALIDATE_SCHEMA = False


def test_load():
    gamedb.GameDB.get_instance()
