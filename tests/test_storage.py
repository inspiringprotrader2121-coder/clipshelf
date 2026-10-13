import pytest

from clipshelf.storage import atomic_write_text


def test_writes_new_file_and_creates_parents(tmp_path):
    target = tmp_path / "nested" / "dir" / "file.txt"
    atomic_write_text(target, "hello")
    assert target.read_text(encoding="utf-8") == "hello"


def test_overwrites_existing_content(tmp_path):
    target = tmp_path / "file.txt"
    atomic_write_text(target, "one")
    atomic_write_text(target, "two")
    assert target.read_text(encoding="utf-8") == "two"


def test_returns_path_and_leaves_no_temp_files(tmp_path):
    target = tmp_path / "file.txt"
    assert atomic_write_text(target, "x") == target
    assert sorted(p.name for p in tmp_path.iterdir()) == ["file.txt"]


def test_failure_is_clean(tmp_path):
    target = tmp_path / "adir"
    target.mkdir()
    with pytest.raises(OSError):
        atomic_write_text(target, "cannot replace a directory")
    assert [p.name for p in tmp_path.iterdir()] == ["adir"]
