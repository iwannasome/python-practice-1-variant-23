"""Повреждённые кадры не должны завершать сервер или менять данные."""

import socket

import pytest
from hypothesis import given, settings, strategies as st

from practice23.client import RpcClient
from practice23.codec import decode, encode
from practice23.protocol import MAX_BODY, pack_frame, receive_frame


@pytest.mark.parametrize("frame", [
    b"\x02\x00\x01\x00\x00\x00\x00",
    b"\x01\x00\x01" + (MAX_BODY + 1).to_bytes(4, "big"),
    pack_frame(1, b"<broken>"),
    pack_frame(1, encode("not-args")),
    pack_frame(1, encode([])),
])
def test_bad_request_keeps_server_alive(rpc_server, frame):
    """Версия, длина, XML и аргументы валидируются до изменения модели."""
    with socket.create_connection(rpc_server.server_address) as sock:
        sock.settimeout(3)
        sock.sendall(frame)
        _, body = receive_frame(sock, reply=True)
        assert decode(body)[0] == "error"
    assert RpcClient(*rpc_server.server_address).list_members() == []


@given(st.recursive(
    st.one_of(st.integers(), st.text()),
    lambda children: st.lists(children, max_size=5), max_leaves=20,
))
@settings(max_examples=60, deadline=None)
def test_generated_xml_roundtrip(value):
    """Произвольная вложенность и Unicode должны возвращаться без потерь."""
    assert decode(encode(value)) == value


@pytest.mark.parametrize("body", [
    b"<unknown/>", b"<int><int>1</int></int>", b"<list>text</list>",
    b'<str bad="1">eA==</str>', b"<str>@@</str>",
    b"<list><int>1</int>extra</list>", b"<int>bad</int>",
])
def test_invalid_xml_grammar(body):
    """Недопустимые элементы, атрибуты и base64 не игнорируются молча."""
    with pytest.raises(ValueError):
        decode(body)
