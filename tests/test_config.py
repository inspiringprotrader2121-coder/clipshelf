import json

import pytest

from clipshelf.config import Config, default_data_dir


def test_defaults_valid():
    config = Config().validate()
    assert config.hotkey == "ctrl+shift+v"
    assert config.max_items == 500


def test_history_path_points_into_data_dir(tmp_path):
    config = Config(data_dir=tmp_path)
    assert config.history_path == tmp_path / "history.json"


def test_save_and_load_roundtrip(tmp_path):
    config = Config(max_items=123, popup_width=640, data_dir=tmp_path)
    path = config.save(tmp_path / "config.json")
    loaded = Config.load(path)
    assert loaded.max_items == 123
    assert loaded.popup_width == 640
    assert loaded.data_dir == tmp_path


def test_load_missing_returns_defaults(tmp_path):
    loaded = Config.load(tmp_path / "nothing.json")
    assert loaded.hotkey == Config().hotkey


def test_load_corrupt_returns_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    assert Config.load(path).hotkey == Config().hotkey


def test_load_ignores_unknown_keys(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"max_items": 10, "mystery": True}), encoding="utf-8")
    assert Config.load(path).max_items == 10


def test_invalid_hotkey_rejected():
    with pytest.raises(ValueError):
        Config(hotkey="ctrl+alt").validate()
    with pytest.raises(ValueError):
        Config(hotkey="ctrl+hyper").validate()
    with pytest.raises(ValueError):
        Config(hotkey="hyper+a").validate()


def test_duplicate_modifier_rejected():
    with pytest.raises(ValueError):
        Config(hotkey="ctrl+ctrl+v").validate()


def test_function_keys_accepted():
    Config(hotkey="ctrl+f13").validate()


def test_bounds_checked():
    with pytest.raises(ValueError):
        Config(max_items=0).validate()
    with pytest.raises(ValueError):
        Config(popup_height=10).validate()


def test_unknown_keys_rejected_by_from_dict():
    config = Config.from_dict({"max_items": 5, "data_dir": "/tmp/x"})
    assert config.max_items == 5
    assert str(config.data_dir) == "/tmp/x"


def test_default_data_dir_on_any_os():
    assert default_data_dir().name in ("clipshelf", ".clipshelf")
