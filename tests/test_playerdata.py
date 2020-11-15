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

    player.monsters = []

    file_handle = io.StringIO()
    player.save(file_handle)
    file_handle.seek(0)
    _ = PlayerData.load(file_handle)

def test_tags(player):
    assert 'in_test' in player.tags
    assert player.can_use_form(player.monsters[0].form)

    player.personal_tags.remove('in_test')
    assert not player.can_use_form(player.monsters[0].form)

def test_max_monsters(player):
    '''Increasing rank should allow for more golems'''

    prev_limit = player.max_monsters
    player.rank += 1
    assert player.max_monsters > prev_limit

def test_rank_tag(player):
    '''Player should have tags based on their current rank'''
    assert 'rank_1' in player.tags
    assert 'rank_2' not in player.tags

    player.rank = 3
    assert 'rank_2' in player.tags
    assert 'rank_3' in player.tags
    assert 'rank_4' not in player.tags
