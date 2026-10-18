"""Проверка двух режимов MBT и неизменности исходного проекта."""

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"correct": (0, "1 passed"), "broken": (1, "1 failed")}


def source_hashes():
    """Зафиксировать исходники и эталон до демонстрации."""
    paths = [*ROOT.glob("src/**/*.py"), ROOT / "tests/test_mbt.py"]
    return {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
    }


@pytest.mark.parametrize("mode", EXPECTED)
def test_mbt_demo_detects_bug_without_changing_sources(mode):
    """Проверить настоящий pytest в копии и неизменность оригиналов."""
    before = source_hashes()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tests/run_mbt_demo.py"), mode],
        cwd=ROOT.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
        check=False,
    )
    code, summary = EXPECTED[mode]
    assert result.returncode == code, result.stdout
    assert summary in result.stdout, result.stdout
    if mode == "broken":
        assert "projection_matches" in result.stdout, result.stdout
        assert "AssertionError" in result.stdout, result.stdout
    assert source_hashes() == before
