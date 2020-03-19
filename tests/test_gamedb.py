def test_load(gdb):
    assert gdb

def test_keys(gdb):
    gdb_keys = [
        'abilities',
        'breeds',
        'monsters',
    ]

    for key in gdb_keys:
        assert key in gdb
