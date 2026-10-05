"""Точка входа для локальной модели; сетевые режимы добавляются этапом 2."""

from .model import Store
from .repl import run_repl

run_repl(Store())
