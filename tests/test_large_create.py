"""Граница размера ответа не должна превращать отказ в скрытую вставку."""

import pytest

from practice23.client import RpcClient, RpcError
from practice23.codec import encode
from practice23.protocol import MAX_BODY


def test_large_create_error_does_not_insert(rpc_server):
    """Допустимый запрос с чрезмерным ответом обязан отказать до вставки."""
    row = [1, 0, "a" * 786336, "ru"]
    assert len(encode([row])) <= MAX_BODY
    assert len(encode(["ok", row])) > MAX_BODY
    client = RpcClient(*rpc_server.server_address)
    with pytest.raises(RpcError):
        client.create_member(row)
    assert client.list_members() == []
