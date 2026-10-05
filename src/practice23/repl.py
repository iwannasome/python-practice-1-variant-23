"""REPL: одна JSON-команда в строке, результат или понятная ошибка.

JSON здесь — удобный локальный синтаксис консоли. На TCP всегда
передаётся XML, как требует вариант. Произвольный Python-код не
исполняется.
"""

import json

from .operations import OPERATIONS, invoke


def run_repl(target):
    """Повторять read-eval-print до quit или EOF, сохраняя объект
    данных.
    """
    print("help — список методов, quit — выход. Формат:")
    print('{"method":"list_members","args":[]}')
    while True:
        try:
            line = input("rpc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line == "quit":
            return
        if line == "help":
            print("\n".join(OPERATIONS))
        elif line:
            execute_line(target, line)


def execute_line(target, line):
    """Показать ошибку команды и продолжить сеанс."""
    try:
        command = json.loads(line)
        if type(command) is not dict:
            raise ValueError("Команда должна быть объектом JSON")
        result = invoke(target, command["method"], command.get("args", []))
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(f"Ошибка: {error}")
