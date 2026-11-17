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


def test_table_falls_back_to_rows():
    node = {"type": "table", "colLabels": ["d6", "Result"], "rows": [["1", "Bad"], ["2", "Worse"]]}
    assert flatten([node]) == [("", ["d6: 1, Result: Bad", "d6: 2, Result: Worse"])]


def test_unknown_object_does_not_crash():
    assert flatten([{"type": "inset", "entries": ["x"]}, {"weird": 1}]) == [("", ["x"])]


def test_empty_sections_dropped():
    assert flatten([{"type": "entries", "name": "Empty", "entries": []}, "text"]) == [("", ["text"])]


def test_roll_cells_render():
    node = {"type": "table", "colLabels": ["d20", "Effect"], "rows": [[{"roll": {"min": 1, "max": 5}}, "Bad"]]}
    assert flatten([node]) == [("", ["d20: 1-5, Effect: Bad"])]
