"""Проверка реального потока команд REPL без исполнения Python-кода."""

from io import StringIO

from practice23.model import Store
from practice23.repl import run_repl


def test_repl_continues_after_errors(monkeypatch, capsys):
    """Ошибочная команда не должна мешать следующему корректному запросу."""
    commands = [
        "help", "", "[]", "{bad}", '{"method":"missing"}',
        '{"method":"get_member","args":[99]}',
        '{"method":"create_member","args":[[1,0,"ip","ru"]]}',
        '{"method":"get_member","args":[1]}', "quit",
    ]
    monkeypatch.setattr("sys.stdin", StringIO("\n".join(commands)))
    run_repl(Store())
    text = capsys.readouterr().out
    assert "Ошибка:" in text
    assert '[1, 0, "ip", "ru"]' in text
    assert "recent_results" in text


def test_repl_exits_at_eof(monkeypatch):
    """Конец перенаправленного stdin завершает консоль без исключения."""
    monkeypatch.setattr("sys.stdin", StringIO(""))
    run_repl(Store())
