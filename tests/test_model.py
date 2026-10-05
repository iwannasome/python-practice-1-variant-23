"""Проверки списка полей, связей, изоляции и строгой границы времени."""

import pytest

from practice23.model import Store


def test_projection_excludes_boundary_and_deduplicates():
    """Замена > на >= или потеря DISTINCT должна нарушить этот тест."""
    store = Store(clock=lambda: 1000)
    store.create_member([1, 1, "127.0.0.1", "ru"])
    store.create_task([1, 2, "input", 1, "tag", 0, 0])
    store.create_response([1, 460, "ok", "ok", "", 1, 10])
    store.create_response([2, 461, "ok", "ok", "", 1, 20])
    store.create_response([3, 999, "ok", "ok", "", 1, 20])
    assert store.recent_results() == [["127.0.0.1", 20, "tag"]]


def test_copy_and_foreign_key():
    """Внешняя мутация не должна менять состояние хранилища."""
    store = Store()
    row = [1, 1, "::1", "ru"]
    store.create_member(row)
    row[2] = "changed"
    store.get_member(1)[2] = "changed"
    store.list_members()[0][2] = "changed"
    assert store.get_member(1) == [1, 1, "::1", "ru"]
    with pytest.raises(ValueError):
        store.create_member([1, 1, "::1", "ru"])
    with pytest.raises(ValueError):
        store.create_task([1, 2, "x", 99, "tag", 0, 0])
    with pytest.raises(ValueError):
        store.get_member(True)
