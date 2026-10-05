"""Воспроизводимая демонстрация всех десяти операций и ошибок."""

import json
from time import time

from .operations import invoke


def demo_commands(now=None):
    """Сформировать учебные записи относительно текущего времени."""
    now = int(time()) if now is None else now
    return [
        ("create_member", [[1, now, "127.0.0.1", "ru-RU"]]),
        ("list_members", []),
        ("get_member", [1]),
        ("create_task", [[1, now, "<input>&данные", 1, "python", 0, 1]]),
        ("list_tasks", []),
        ("get_task", [1]),
        ("create_response", [[1, now, "готово", "ok", "", 1, 23]]),
        ("list_responses", []),
        ("get_response", [1]),
        ("recent_results", []),
        ("get_member", [999]),
        ("create_member", [[1, now, "127.0.0.1", "ru-RU"]]),
        ("create_task", [[2, now, "x", 999, "tag", 0, 0]]),
        ("create_response", [[2, now, "x", "ok", "", 1, -1]]),
        ("create_member", [[2, "не число", "::1", "ru"]]),
    ]


def demonstrate(target):
    """Напечатать вызовы, фактические результаты и ожидаемые ошибки."""
    for name, args in demo_commands():
        print(f"> {name} args={json.dumps(args, ensure_ascii=False)}")
        try:
            result = invoke(target, name, args)
            print(json.dumps(result, ensure_ascii=False))
        except ValueError as error:
            print(f"Ожидаемая ошибка: {error}")
