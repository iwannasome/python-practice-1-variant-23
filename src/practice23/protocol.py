"""Кадрирование TCP по таблице 23: запрос 1+2+4, ответ 1+1+5 байт.

TCP — поток байтов. Один sendall может потребовать нескольких recv.
Длина описывает байты XML, а не число символов строки. Все числа
unsigned, порядок big-endian. Лимит 1 MiB защищает память до чтения
тела.
"""

VERSION = 1
HEADER_SIZE = 7
MAX_BODY = 1024 * 1024
TIMEOUT = 3.0
ERROR_CODE = 0


def pack_frame(code, body, reply=False):
    """Построить заголовок нужного направления и добавить XML-байты."""
    if len(body) > MAX_BODY:
        raise ValueError("Тело превышает 1 MiB")
    code_size, size_size = (1, 5) if reply else (2, 4)
    return (
        bytes([VERSION])
        + code.to_bytes(code_size, "big")
        + len(body).to_bytes(size_size, "big")
        + body
    )


def read_exact(sock, size):
    """Прочитать ровно size байт; EOF посреди кадра означает ошибку."""
    result = bytearray()
    while len(result) < size:
        part = sock.recv(size - len(result))
        if not part:
            raise ValueError("Соединение закрыто до конца кадра")
        result.extend(part)
    return bytes(result)


def receive_frame(sock, reply=False):
    """Прочитать заголовок, проверить версию и получить тело."""
    header = read_exact(sock, HEADER_SIZE)
    if header[0] != VERSION:
        raise ValueError("Неподдерживаемая версия протокола")
    code_end = 2 if reply else 3
    code = int.from_bytes(header[1:code_end], "big")
    size = int.from_bytes(header[code_end:], "big")
    if size > MAX_BODY:
        raise ValueError("Тело превышает 1 MiB")
    return code, read_exact(sock, size)
