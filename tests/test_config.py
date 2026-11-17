import os
import tempfile
import unittest.mock as mock
from pathlib import Path

from tcard.config import Config, ConfigError, load


def test_missing_config_uses_defaults():
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp}):
        config = load()
        assert (config.systems, config.kinds, config.prefer, config.cols) == (
            ["dnd:5e"],
            ["spell"],
            ["XPHB", "PHB"],
            32,
        )


def test_config_overrides():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text('cols = 38\nprefer = ["PHB"]\n')
        config = load(path)
        assert config.cols == 38 and config.prefer == ["PHB"]


def test_bad_toml_raises_config_error():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text("cols = [")
        try:
            load(path)
        except ConfigError:
            return
    raise AssertionError("expected ConfigError")


def test_bad_cols_raises_config_error():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text("cols = 4\n")
        try:
            load(path)
        except ConfigError:
            return
    raise AssertionError("expected ConfigError")


def test_bad_kinds_type_raises_config_error():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text('kinds = "spell"\n')
        try:
            load(path)
        except ConfigError:
            return
    raise AssertionError("expected ConfigError")


def test_defaults_are_not_shared_between_instances():
    first, second = Config(), Config()
    first.systems.append("pf1e")
    assert second.systems == ["dnd:5e"]
