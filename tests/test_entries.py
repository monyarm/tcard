from tcard.model import Table
from tcard.sources.fivee.entries import flatten


def test_strings_become_paragraphs():
    assert flatten(["one", "two"]) == [("", ["one", "two"])]


def test_named_entries_becomes_section():
    got = flatten(["intro", {"type": "entries", "name": "At Higher Levels", "entries": ["more"]}])
    assert got == [("", ["intro"]), ("At Higher Levels", ["more"])]


def test_list_items_are_bulleted():
    assert flatten([{"type": "list", "items": ["a", "b"]}]) == [("", ["- a", "- b"])]


def test_nested_list_indents():
    node = {"type": "list", "items": ["a", {"type": "list", "items": ["b"]}]}
    assert flatten([node]) == [("", ["- a", "- b"])]


def test_table_becomes_table_object():
    node = {"type": "table", "colLabels": ["d6", "Result"], "rows": [["1", "Bad"], ["2", "Worse"]]}
    sections = flatten([node])
    table = sections[0][1][0]
    assert isinstance(table, Table)
    assert table.header is True
    assert table.rows == [["d6", "Result"], ["1", "Bad"], ["2", "Worse"]]


def test_unknown_object_does_not_crash():
    assert flatten([{"type": "inset", "entries": ["x"]}, {"weird": 1}]) == [("", ["x"])]


def test_empty_sections_dropped():
    assert flatten([{"type": "entries", "name": "Empty", "entries": []}, "text"]) == [("", ["text"])]


def test_roll_cells_render():
    node = {"type": "table", "colLabels": ["d20", "Effect"], "rows": [[{"roll": {"min": 1, "max": 5}}, "Bad"]]}
    rows = flatten([node])[0][1][0].rows
    assert rows == [["d20", "Effect"], ["1-5", "Bad"]]
