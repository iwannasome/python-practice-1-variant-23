"""Проверка формальных ограничений методички без сторонних библиотек."""

import ast
import io
import tokenize
from pathlib import Path

MAX_LINES = 1000
MAX_WIDTH = 79
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7


def is_number_literal(node):
    """Распознать числовой литерал, включая значение со знаком."""
    if isinstance(node, ast.UnaryOp):
        return is_number_literal(node.operand)
    return isinstance(node, ast.Constant) and type(node.value) in (int, float)


def audit_comparison(node, path):
    """Проверить отсутствие числовых литералов в сравнении."""
    operands = [node.left, *node.comparators]
    assert not any(map(is_number_literal, operands)), (
        path,
        node.lineno,
        "Числовой литерал в сравнении",
    )


def audit_function(node, path):
    """Проверить длину функции и количество её аргументов."""
    length = node.end_lineno - node.lineno + 1
    assert length <= MAX_FUNCTION_LINES, (path, node.name, length)
    args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
    count = len(args) - bool(args and args[0].arg in {"self", "cls"})
    assert count <= MAX_ARGUMENTS, (path, node.name, count)


def audit_file(path):
    """Проверить размер файла, ширину, функции и отсутствие #
    комментариев.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) <= MAX_LINES, path
    assert all(len(line) <= MAX_WIDTH for line in lines), path
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    assert not any(token.type == tokenize.COMMENT for token in tokens), path
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Compare):
            audit_comparison(node, path)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            audit_function(node, path)


def main():
    """Проверить весь Python-код репозитория, включая автоматические
    тесты.
    """
    root = Path(__file__).resolve().parents[1]
    files = sorted(root.glob("src/**/*.py")) + sorted(root.glob("tests/*.py"))
    for path in files:
        audit_file(path)
    print(f"PASS: {len(files)} файлов, строки <=79, функции <=40")
    print("аргументы <=7, обычных комментариев нет, файлы <=1000 строк")
    print("PASS: нет числовых литералов в операндах сравнений")


if __name__ == "__main__":
    main()
