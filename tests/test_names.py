from tcard.names import normalize, split_path
from tcard.sources.base import Kind


class _Kind(Kind):
    def records(self, refresh: bool = False) -> list[dict]:
        return []

    def card(self, record: dict):
        raise NotImplementedError


def test_normalize_underscores_and_apostrophes():
    assert normalize("Tasha\u2019s_Hideous  Laughter") == "tashas hideous laughter"
    assert normalize("Second__Wind") == "second wind"
    assert normalize("  Fireball ") == "fireball"


def test_split_path():
    assert split_path("rogue:assassin:assassinate") == ["rogue", "assassin", "assassinate"]
    assert split_path("fighter: second_wind") == ["fighter", "second wind"]
    assert split_path("fighter::") == ["fighter"]


def test_matches_prefers_exact_then_prefix():
    kind = _Kind()
    records = [{"name": "Fireball"}, {"name": "Fire Bolt"}, {"name": "Fireball"}]
    assert kind.matches(records, "fireball") == [records[0], records[2]]
    assert kind.matches(records, "fire_b") == [records[1]]
    assert kind.matches(records, "nope") == []
