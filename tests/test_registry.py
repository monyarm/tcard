from tcard.sources import registry


def test_registry_has_5e_spell():
    kinds = registry.kinds("dnd:5e")
    assert "spell" in kinds
    assert hasattr(kinds["spell"], "card")
    assert hasattr(kinds["spell"], "records")


def test_registry_unknown_system_raises():
    try:
        registry.kinds("nope")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_systems_lists_5e():
    assert "dnd:5e" in registry.systems()
