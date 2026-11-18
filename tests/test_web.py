"""Web UI: index/facets, the CLI runner and the print pipe, no sockets or network."""

import unittest.mock as mock

from tcard.web import data, print as printing, server


class FakeKind:
    def __init__(self, records):
        self._records = records
        self.refreshed = []

    def records(self, refresh=False):
        self.refreshed.append(refresh)
        return self._records

    def display(self, record):
        return record["name"]


RECORDS = [
    {"name": "Fireball", "source": "PHB", "level": 3, "school": "Evocation", "cost": 1},
    {"name": "Fire Bolt", "source": "PHB", "level": 0, "school": "Evocation", "cost": 2},
    {"name": "Cure Wounds", "source": "XPHB", "level": 1, "school": "Abjuration", "cost": 3},
    {"name": "Shield", "source": "PHB", "level": 1, "school": "Abjuration", "cost": 4},
]


def _fake_registry(kind="spell"):
    fake = FakeKind(RECORDS)
    kinds = lambda system: {kind: fake}
    return mock.patch.object(data.registry, "kinds", kinds), fake


def test_facets_keep_declared_keys_and_skip_free_text():
    patch, _ = _fake_registry()
    data._CACHE.clear()
    with patch:
        built = data.build("dnd:5e", "spell")
    assert list(built.facets)[:3] == ["source", "level", "school"]
    # `cost` is not declared but has few values, so it is picked up on its own.
    assert "cost" in built.facets
    assert [(item["value"], item["count"]) for item in built.facets["source"]] \
        == [("PHB", 3), ("XPHB", 1)]
    # Numeric values sort as numbers, not as text.
    assert [item["value"] for item in built.facets["level"]] == ["0", "1", "3"]


def test_search_matches_name_and_facet_together():
    patch, _ = _fake_registry()
    data._CACHE.clear()
    with patch:
        found = data.search("dnd:5e", "spell", "fire")
        assert found["total"] == 2
        narrowed = data.search("dnd:5e", "spell", "fire", {"level": ["3"]})
        assert [row["name"] for row in narrowed["rows"]] == ["Fireball"]
        assert narrowed["total"] == 1
        # Counts stay over the whole kind, not the filtered slice.
        assert narrowed["count"] == 4
        assert len(narrowed["facets"]["source"]) == 2


def test_search_pages_without_dropping_rows():
    patch, _ = _fake_registry()
    data._CACHE.clear()
    with patch:
        first = data.search("dnd:5e", "spell", limit=2)
        second = data.search("dnd:5e", "spell", limit=2, offset=2)
    assert len(first["rows"]) == 2 and len(second["rows"]) == 2
    assert {row["name"] for row in first["rows"]} | {row["name"] for row in second["rows"]} \
        == {record["name"] for record in RECORDS}


def test_index_is_cached_until_refresh():
    patch, fake = _fake_registry()
    data._CACHE.clear()
    with patch:
        data.index("dnd:5e", "spell")
        data.index("dnd:5e", "spell")
        assert fake.refreshed == [False]
        data.index("dnd:5e", "spell", refresh=True)
        assert fake.refreshed == [False, True]


def test_pf1_section_widens_only_as_far_as_needed():
    assert data._pf1_section("https://www.d20pfsrd.com/magic/all-spells/a/abeyance/", 2) \
        == "magic/all-spells"
    assert data._pf1_section("https://www.d20pfsrd.com/feats/achievement-feats/x/", 2) \
        == "feats/achievement-feats"
    assert data._pf1_section("https://www.d20pfsrd.com/classes/core-classes/rogue/rogue-talents/x/", 3) \
        == "classes/core-classes/rogue"


def test_pf2_pack_is_the_directory_under_packs():
    assert data._pf2_pack("/cache/pf2/repo/packs/pf2e/spells/focus/x.json") == "spells"
    assert data._pf2_pack("/cache/pf2/repo/packs/pf2e/pathfinder-monster-core/x.json") \
        == "pathfinder-monster-core"
    assert data._pf2_pack("") == ""


def test_source_reads_a_dict_book_code():
    assert data.source({"source": "PHB"}) == "PHB"
    assert data.source({"source": {"book": "BH", "page": 6}}) == "BH"
    assert data.source({}) == ""


def test_unknown_kind_raises_key_error():
    patch, _ = _fake_registry()
    data._CACHE.clear()
    with patch:
        try:
            data.build("dnd:5e", "nope")
        except KeyError as exc:
            assert exc.args[0] == "nope"
        else:
            raise AssertionError("expected KeyError")


def test_argv_carries_source_cols_and_brief():
    command = printing.argv("dnd:5e", "spell", "Fireball", "PHB", 40, True)
    assert command[1:3] == ["-m", "tcard"]
    assert command[command.index("--cols") + 1] == "40"
    assert command[command.index("--source") + 1] == "PHB"
    assert command[-1] == "--brief"


def _run_stub(returncode=0, stdout=b"CARD\n", stderr=b""):
    return mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr)


def test_card_text_returns_cli_stdout():
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return _run_stub()

    with mock.patch.object(printing.subprocess, "run", fake_run):
        assert printing.card_text("dnd:5e", "spell", "Fireball") == "CARD\n"
    assert calls[0][0] == printing.sys.executable
    assert calls[0][3:6] == ["dnd:5e", "spell", "Fireball"]


def test_card_text_surfaces_the_last_stderr_line():
    stub = _run_stub(returncode=1, stdout=b"", stderr=b"tcard: no match for 'x'\nmore\n")
    with mock.patch.object(printing.subprocess, "run", lambda *a, **k: stub):
        try:
            printing.card_text("dnd:5e", "spell", "x")
        except printing.PrintError as exc:
            assert str(exc) == "more" and exc.code == 1
        else:
            raise AssertionError("expected PrintError")


def test_card_text_rejects_out_of_range_cols():
    try:
        printing.card_text("dnd:5e", "spell", "x", cols=500)
    except printing.PrintError as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected PrintError")


def test_print_pipes_the_cli_output_into_tp():
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs.get("input")))
        if len(calls) == 1:
            return _run_stub(stdout=b"FIREBALL\n=====\n")
        return _run_stub(stdout=b"")

    with mock.patch.object(printing.shutil, "which", lambda name: "/bin/tp"), \
         mock.patch.object(printing.subprocess, "run", fake_run):
        text = printing.card_text("dnd:5e", "spell", "Fireball")
        result = printing.print_card(text)
    assert result["ok"] and result["tp"] == "/bin/tp"
    assert calls[0][0][0] == printing.sys.executable
    assert calls[1][0] == ["/bin/tp"]
    assert calls[1][1] == b"FIREBALL\n=====\n"


def test_dry_run_never_calls_tp():
    with mock.patch.object(printing.subprocess, "run") as run:
        result = printing.print_card("CARD\n", dry_run=True)
    assert result["dry_run"] is True
    run.assert_not_called()


def test_missing_tp_is_reported_not_crashed():
    with mock.patch.object(printing.shutil, "which", lambda name: None):
        try:
            printing.print_card("CARD\n")
        except printing.PrintError as exc:
            assert exc.code == 3 and "tp" in str(exc)
        else:
            raise AssertionError("expected PrintError")


def test_status_codes_follow_the_cli_exit_codes():
    assert server._status(2) == 400
    assert server._status(3) == 502
    assert server._status(1) == 404
