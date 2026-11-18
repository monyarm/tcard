import contextlib
import io
import unittest.mock as mock

from tcard import cli
from tcard.config import Config
from tcard.model import Card, LineKind
from tcard.sources.base import Kind

RECORDS = [
    {"name": "Fireball", "source": "XPHB"},
    {"name": "Fireball", "source": "PHB"},
    {"name": "Fire Bolt", "source": "XPHB"},
    {"name": "Shield", "source": "XPHB"},
]


class FakeKind(Kind):
    id = "spell"

    def records(self, refresh: bool = False):
        return RECORDS

    def card(self, record):
        return Card(record["name"], "", [("Source", str(record.get("source")))], [("", ["text"])])


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(cli.registry, "kinds", lambda system: {"spell": FakeKind()}), mock.patch.object(
        cli.config, "load", lambda: Config(kinds=["spell"])
    ), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_split_terms_full():
    assert cli.split_terms(["dnd:5e", "spell", "fireball"], ["dnd:5e"], ["spell"]) == ("dnd:5e", "spell", "fireball")


def test_split_terms_system_only():
    assert cli.split_terms(["dnd:5e", "fireball"], ["dnd:5e"], ["spell"]) == ("dnd:5e", None, "fireball")


def test_split_terms_kind_only():
    assert cli.split_terms(["spell", "fire", "ball"], ["dnd:5e"], ["spell"]) == ("dnd:5e", "spell", "fire ball")


def test_split_terms_name_only():
    assert cli.split_terms(["fireball"], ["dnd:5e"], ["spell"]) == ("dnd:5e", None, "fireball")


def test_split_terms_missing_name():
    try:
        cli.split_terms(["dnd:5e"], ["dnd:5e"], ["spell"])
    except Exception as exc:
        assert "missing card name" in str(exc)
        return
    raise AssertionError("expected error")


def test_prefer_order():
    assert cli.pick(RECORDS[:2], ["XPHB", "PHB"], None)["source"] == "XPHB"


def test_prefer_falls_back_to_first_match():
    assert cli.pick(RECORDS[:2], ["DMG"], None)["source"] in ("XPHB", "PHB")


def test_source_override():
    assert cli.pick(RECORDS[:2], ["XPHB"], "PHB")["source"] == "PHB"


def test_source_override_missing():
    assert cli.pick(RECORDS[:2], ["XPHB"], "DMG") is None


def test_find_prefix():
    assert [record["name"] for record in cli.find(RECORDS, "fire b")] == ["Fire Bolt"]


def test_find_exact_beats_prefix():
    assert cli.find(RECORDS, "fireball") == RECORDS[:2]


def test_main_prints_card():
    code, out, _ = run(["fireball"])
    assert code == 0
    assert out.startswith("FIREBALL\n")
    assert "=====" in out


def test_main_unknown_exits_1():
    code, _, err = run(["nope"])
    assert code == 1
    assert "no match" in err


def test_main_ambiguous_exits_1():
    code, _, err = run(["fire"])
    assert code == 1
    assert "ambiguous" in err and "Fire Bolt" in err


def test_main_all_lists_sources():
    code, out, _ = run(["--all", "fireball"])
    assert code == 0
    assert "XPHB" in out and "PHB" in out


def test_main_source_flag():
    code, out, _ = run(["--source", "PHB", "fireball"])
    assert code == 0
    assert "PHB" in out


def test_matches_falls_back_to_substring():
    kind = FakeKind()
    assert [record["name"] for record in kind.matches(RECORDS, "bolt")] == ["Fire Bolt"]


def test_matches_prefers_a_prefix_over_a_later_substring():
    kind = FakeKind()
    records = [{"name": "Bolt"}, {"name": "Fire Bolt"}]
    assert [record["name"] for record in kind.matches(records, "bol")] == ["Bolt"]


def test_all_searches_every_system():
    table = {"dnd:5e": {"spell": FakeKind()}, "cp:2020": {"weapon": FakeKind()}}
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(cli.registry, "systems", lambda: ["dnd:5e", "cp:2020"]), mock.patch.object(
        cli.registry, "kinds", lambda system: table[system]
    ), mock.patch.object(cli.config, "load", lambda: Config(kinds=["spell"])), contextlib.redirect_stdout(
        out
    ), contextlib.redirect_stderr(err):
        code = cli.main(["--all", "fire"])
    text = out.getvalue()
    assert code == 0
    assert "(dnd:5e spell" in text
    assert "(cp:2020 weapon" in text


def test_main_cols_flag():
    code, out, _ = run(["--cols", "20", "fireball"])
    assert code == 0
    assert max(len(line) for line in out.splitlines()) <= 20


def test_main_brief_drops_body():
    code, out, _ = run(["--brief", "fireball"])
    assert code == 0
    assert "text" not in out


def test_main_explicit_system_and_kind():
    code, out, _ = run(["dnd:5e", "spell", "fireball"])
    assert code == 0 and "FIREBALL" in out


def test_unknown_system_selector_is_usage_error():
    code, _, err = run(["dnd:9e", "fireball"])
    assert code == 2
    assert "unknown system 'dnd:9e'" in err and "dnd:5e" in err


def test_exit_codes_map():
    code, _, err = run(["dnd:5e", "spell", "nope"])
    assert code == 1 and "dnd:5e" not in err


def test_unknown_kind_is_no_match():
    code, _, err = run(["dnd:5e", "feat", "power attack"])
    assert code == 1
    assert "no match" in err


def test_bad_cols_is_usage_error():
    code, _, err = run(["--cols", "4", "fireball"])
    assert code == 2
    assert "cols" in err


def test_out_of_range_cols_is_usage_error():
    code, _, err = run(["--cols", "3", "fireball"])
    assert code == 2
    assert "between 8 and 200" in err
