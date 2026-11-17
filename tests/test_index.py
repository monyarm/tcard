import json
import os
import tempfile
import unittest.mock as mock
from pathlib import Path

from tcard.errors import TcardError
from tcard.sources.fivee import index

INDEX_URL = f"{index.BASE}/index.json"
BOOK_URL = f"{index.BASE}/spells-phb.json"


def _fake_get(files, calls):
    def get(url):
        calls.append(url)
        return files[url].encode() if isinstance(files[url], str) else files[url]

    return get


def test_spell_records_caches_and_merges():
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"XDG_CACHE_HOME": tmp}):
        files = {
            INDEX_URL: '{"PHB": "spells-phb.json"}',
            BOOK_URL: '{"spell": [{"name": "Fireball", "source": "PHB"}]}',
        }
        calls = []
        with mock.patch.object(index, "_get", _fake_get(files, calls)):
            records = index.spell_records()
            assert [record["name"] for record in records] == ["Fireball"]
            assert index.spell_records() == records
        assert len(calls) == 2, calls
        assert Path(tmp, "tcard", "dnd-5e", "index.json").exists()
        assert Path(tmp, "tcard", "dnd-5e", "manifest.json").exists()


def test_changed_index_refetches_books():
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"XDG_CACHE_HOME": tmp}):
        files = {
            INDEX_URL: '{"PHB": "spells-phb.json"}',
            BOOK_URL: '{"spell": [{"name": "Fireball", "source": "PHB"}]}',
        }
        calls = []
        with mock.patch.object(index, "_get", _fake_get(files, calls)):
            index.spell_records()
        assert calls.count(BOOK_URL) == 1

        # A stale cached index must not refetch books, even with new names in it.
        files[INDEX_URL] = '{"PHB": "spells-phb.json", "XPHB": "spells-phb.json"}'
        calls.clear()
        with mock.patch.object(index, "_get", _fake_get(files, calls)):
            index.spell_records()
        assert calls == []

        # The cached index changed on disk (e.g. --refresh wrote it): books refetch once.
        Path(tmp, "tcard", "dnd-5e", "index.json").write_text(files[INDEX_URL])
        calls.clear()
        with mock.patch.object(index, "_get", _fake_get(files, calls)):
            index.spell_records()
        assert calls == [BOOK_URL], calls


def test_corrupt_index_cache_exits_3():
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"XDG_CACHE_HOME": tmp}):
        target = Path(tmp, "tcard", "dnd-5e", "index.json")
        target.parent.mkdir(parents=True)
        target.write_text("{not json")
        try:
            index.spell_records()
        except TcardError as exc:
            assert exc.exit_code == 3
            return
        raise AssertionError("expected TcardError")


def test_network_error_exits_3():
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"XDG_CACHE_HOME": tmp}):
        with mock.patch.object(index, "urlopen", side_effect=OSError("no route")):
            try:
                index.spell_records()
            except TcardError as exc:
                assert exc.exit_code == 3
                assert "5e.tools" in str(exc)
                return
        raise AssertionError("expected TcardError")


def test_dedupe_keeps_first():
    records = [{"name": "A", "source": "X"}, {"name": "A", "source": "X"}, {"name": "A", "source": "P"}]
    assert index._dedupe(records) == [records[0], records[2]]


def test_cache_dir_honours_xdg():
    with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": "/tmp/xyz"}):
        assert index.cache_dir() == Path("/tmp/xyz/tcard/dnd-5e")


def test_book_payload_is_parsed():
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"XDG_CACHE_HOME": tmp}):
        files = {
            INDEX_URL: '{"PHB": "spells-phb.json"}',
            BOOK_URL: json.dumps({"spell": [{"name": "Fireball", "source": "PHB", "level": 3}]}),
        }
        with mock.patch.object(index, "_get", _fake_get(files, [])):
            assert index.spell_records()[0]["level"] == 3
