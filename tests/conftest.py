"""Фикстура реального TCP-сервера на свободном локальном порту."""

import threading

import pytest

from practice23.model import Store
from practice23.server import RpcServer


@pytest.fixture
def rpc_server():
    """Освободить порт и дождаться серверного потока даже при ошибке
    теста.
    """
    with RpcServer(("127.0.0.1", 0), Store(clock=lambda: 1000)) as server:
        thread = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.01},
        )
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join()
