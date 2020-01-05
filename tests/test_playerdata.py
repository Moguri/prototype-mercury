import io

from game.playerdata import PlayerData


def test_save_load_basic(player):
    ''' Simple round-trip save/load'''

    file_handle = io.StringIO()
    player.save(file_handle)
    file_handle.seek(0)
    _ = PlayerData.load(file_handle)


def test_save_load_no_monster(player):
    '''Save/load when player has no monster'''

    player.monster = None

    file_handle = io.StringIO()
    player.save(file_handle)
    file_handle.seek(0)
    _ = PlayerData.load(file_handle)
