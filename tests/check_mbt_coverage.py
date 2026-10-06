"""Проверка десяти операций по JSON-отчёту отдельного MBT-запуска."""

import ast
import json
import sys
from pathlib import Path

NO_MISSING = 0

METHODS = (
    "create_member",
    "list_members",
    "get_member",
    "create_task",
    "list_tasks",
    "get_task",
    "create_response",
    "list_responses",
    "get_response",
    "recent_results",
)


def check_file(filename, data):
    """У каждой публичной операции должны быть исполнены все строки
    тела.
    """
    source = Path(filename).read_text(encoding="utf-8")
    executed = set(data["executed_lines"])
    missing = set(data["missing_lines"])
    methods = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name in METHODS
    ]
    assert len(methods) == len(METHODS), filename
    for method in methods:
        body = set(range(method.lineno + 1, method.end_lineno + 1))
        assert executed & body, (filename, method.name, "не вызывался")
        assert not missing & body, (filename, method.name, "пропущены строки")
        print(f"PASS {Path(filename).name}: {method.name}")


def main():
    """Проверить 100% ветвей модели и валидации."""
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    assert report["meta"]["branch_coverage"], "Нужен coverage --branch"
    for name in ("model", "client"):
        filename = f"src/practice23/{name}.py"
        check_file(filename, report["files"][filename])
    for name in ("model", "schema"):
        summary = report["files"][f"src/practice23/{name}.py"]["summary"]
        assert summary["missing_lines"] == NO_MISSING, name
        assert summary["missing_branches"] == NO_MISSING, name
    print("PASS: 10/10 методов модели и клиента; model/schema 100% ветвей")


if __name__ == "__main__":
    main()
