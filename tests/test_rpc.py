"""Сквозная проверка всех методов и отказов через настоящие сокеты."""

import socket
from concurrent.futures import ThreadPoolExecutor

import pytest

from practice23.client import RpcClient, RpcError
from practice23.codec import decode, encode
from practice23.protocol import pack_frame, receive_frame


def test_all_ten_methods(rpc_server):
    """Проверить целый цикл создания и чтения трёх сущностей и выборки."""
    client = RpcClient(*rpc_server.server_address)
    member = [1, 900, "::1", "ru"]
    task = [1, 900, "<&>", 1, "tag", 0, 1]
    response = [1, 999, "ok", "ok", "", 1, 15]
    assert client.create_member(member) == member
    assert client.list_members() == [member]
    assert client.get_member(1) == member
    assert client.create_task(task) == task
    assert client.list_tasks() == [task]
    assert client.get_task(1) == task
    assert client.create_response(response) == response
    assert client.list_responses() == [response]
    assert client.get_response(1) == response
    assert client.recent_results() == [["::1", 15, "tag"]]
    with pytest.raises(RpcError):
        client.create_member(member)


def test_unknown_operation_and_server_survival(rpc_server):
    """Код 65535 нельзя обрезать до байта: ошибка возвращается с кодом 0."""
    with socket.create_connection(rpc_server.server_address) as sock:
        sock.sendall(pack_frame(65535, encode([])))
        code, body = receive_frame(sock, reply=True)
        assert code == 0
        assert decode(body)[0] == "error"
    assert RpcClient(*rpc_server.server_address).list_members() == []


def test_concurrent_duplicate_is_atomic(rpc_server):
    """Два клиента не могут успешно создать один и тот же ключ."""
    client = RpcClient(*rpc_server.server_address)
    def create():
        """Вернуть наблюдаемый результат конкурентного создания."""
        try:
            client.create_member([1, 0, "::1", "ru"])
            return "ok"
        except RpcError:
            return "error"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: create(), range(2)))
    assert sorted(outcomes) == ["error", "ok"]
    assert len(client.list_members()) == 1
