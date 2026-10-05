"""Независимые проверки байтового формата и XML-кругового преобразования."""

import socket
import threading

import pytest

from practice23.codec import decode, encode
from practice23.protocol import pack_frame, receive_frame


def test_exact_asymmetric_headers():
    """Неверные размеры полей и endian нарушат эти буквальные эталоны."""
    assert pack_frame(258, b"abc") == b"\x01\x01\x02\x00\x00\x00\x03abc"
    assert pack_frame(10, b"abc", reply=True) == (
        b"\x01\x0a\x00\x00\x00\x00\x03abc"
    )


def test_xml_preserves_unicode_controls_and_lists():
    """Кодек должен сохранять русские строки, XML-символы и пустые списки."""
    value = [1, -2, ["Привет <&>\r\n\x00", "", []]]
    assert decode(encode(value)) == value
    with pytest.raises(ValueError):
        decode(b'<!DOCTYPE x [<!ENTITY a "boom">]><x>&a;</x>')


def test_fragmented_tcp_and_truncated_body():
    """recv не обязан возвращать целый кадр за один вызов."""
    left, right = socket.socketpair()
    frame = pack_frame(1, b"abc")
    def send_fragments():
        """Передать кадр по байту, затем закрыть отправляющую сторону."""
        with left:
            for byte in frame:
                left.sendall(bytes([byte]))
    worker = threading.Thread(target=send_fragments)
    worker.start()
    with right:
        assert receive_frame(right) == (1, b"abc")
    worker.join()
    left, right = socket.socketpair()
    with left, right:
        left.sendall(frame[:-1])
        left.shutdown(socket.SHUT_WR)
        with pytest.raises(ValueError):
            receive_frame(right)
