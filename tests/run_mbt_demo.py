"""Запуск одного MBT на исправной и испорченной копиях модели."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

EXPECTED_MATCHES = 1
SETUP_ERROR = 2
CORRECT_BLOCK = (
    "                if row not in result:\n"
    "                    result.append(row)"
)
BROKEN_BLOCK = "                result.append(row)"


def remove_deduplication(path):
    """Внести ровно одну ошибку в копию, сохранив проверки времени."""
    source = path.read_text(encoding="utf-8")
    if source.count(CORRECT_BLOCK) != EXPECTED_MATCHES:
        raise ValueError("Блок удаления дубликатов изменён: показ отменён")
    path.write_text(
        source.replace(CORRECT_BLOCK, BROKEN_BLOCK), encoding="utf-8"
    )


def prepare_project(root, target, mode):
    """Скопировать исходники, MBT и настройки в пустую папку."""
    shutil.copytree(
        root / "src",
        target / "src",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (target / "tests").mkdir()
    shutil.copy2(root / "tests/test_mbt.py", target / "tests/test_mbt.py")
    shutil.copy2(root / "pyproject.toml", target / "pyproject.toml")
    if mode == "broken":
        remove_deduplication(target / "src/practice23/model.py")


def run_demo(mode):
    """Запустить pytest и удалить временную копию после показа."""
    root = Path(__file__).resolve().parents[1]
    with TemporaryDirectory(prefix="practice23-mbt-") as directory:
        target = Path(directory)
        prepare_project(root, target, mode)
        print(
            f"MBT mode: {mode}. Tests and reference model are unchanged.",
            flush=True,
        )
        if mode == "broken":
            print(
                "Deduplication removed in the copy. Expect FAILED.", flush=True
            )
        else:
            print("Correct model in the copy. Expect PASSED.", flush=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_mbt.py",
                "-vv",
                "--tb=short",
                "-o",
                "addopts=",
                "-p",
                "no:cacheprovider",
            ],
            cwd=target,
            env={**os.environ, "PYTEST_ADDOPTS": ""},
            check=False,
        )
        return result.returncode


def main():
    """Выбрать режим без изменения основного проекта или тестов."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("correct", "broken"))
    args = parser.parse_args()
    try:
        return run_demo(args.mode)
    except (OSError, ValueError) as error:
        print(f"Ошибка подготовки демонстрации: {error}", file=sys.stderr)
        return SETUP_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
