"""Проверка формальных ограничений методички без сторонних библиотек."""

import ast
import io
from pathlib import Path
import tokenize

MAX_LINES = 1000
MAX_WIDTH = 80
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7


def audit_file(path):
    """Проверить размер файла, ширину, функции и отсутствие # комментариев."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) <= MAX_LINES, path
    assert all(len(line) <= MAX_WIDTH for line in lines), path
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    assert not any(token.type == tokenize.COMMENT for token in tokens), path
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = node.end_lineno - node.lineno + 1
            assert length <= MAX_FUNCTION_LINES, (path, node.name, length)
            args = (
                node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            )
            count = len(args) - bool(args and args[0].arg in {"self", "cls"})
            assert count <= MAX_ARGUMENTS, (path, node.name, count)


def main():
    """Проверить весь Python-код репозитория, включая автоматические тесты."""
    root = Path(__file__).resolve().parents[1]
    files = sorted(root.glob("src/**/*.py")) + sorted(root.glob("tests/*.py"))
    for path in files:
        audit_file(path)
    print(f"PASS: {len(files)} файлов; строки <=80; функции <=40;")
    print("аргументы <=7; обычных комментариев нет; файлы <=1000 строк")


if __name__ == "__main__":
    main()
