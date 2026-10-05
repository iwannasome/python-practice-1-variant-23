"""Клиент RPC с теми же десятью методами, что у Store.

Каждый вызов открывает TCP-соединение, отправляет XML-кадр, читает ответ
и гарантированно закрывает сокет. Ошибки модели передаются как RpcError,
который наследует ValueError и удобно обрабатывается тем же REPL.
"""

from socket import create_connection

from .codec import decode, encode
from .operations import CODES
from .protocol import TIMEOUT, pack_frame, receive_frame

PAIR_SIZE = 2


class RpcError(ValueError):
    """Контролируемая ошибка, полученная от удалённой модели."""


class RpcClient:
    """Адресуемый клиент; состояние данных хранится только на сервере."""

    def __init__(self, host="127.0.0.1", port=8023, timeout=TIMEOUT):
        """Сохранить адрес и тайм-аут; соединение открывается при вызове."""
        self.address = (host, port)
        self.timeout = timeout

    def _call(self, method, args):
        """Проверить ответ и отделить ошибку от успешного результата."""
        code = CODES[method]
        request = pack_frame(code, encode(args))
        with create_connection(self.address, timeout=self.timeout) as sock:
            sock.sendall(request)
            reply_code, body = receive_frame(sock, reply=True)
        if reply_code != code:
            raise ValueError("Код ответа не совпадает с кодом запроса")
        payload = decode(body)
        if type(payload) is not list or len(payload) != PAIR_SIZE:
            raise ValueError("Неверная структура ответа")
        status, result = payload
        if status == "error":
            raise RpcError(str(result))
        if status != "ok":
            raise ValueError("Неизвестный статус ответа")
        return result

    def create_member(self, row):
        """Удалённо создать Member из списка четырёх полей."""
        return self._call("create_member", [row])

    def list_members(self):
        """Удалённо получить все записи Member."""
        return self._call("list_members", [])

    def get_member(self, uid):
        """Удалённо получить Member по uid."""
        return self._call("get_member", [uid])

    def create_task(self, row):
        """Удалённо создать Task из списка семи полей."""
        return self._call("create_task", [row])

    def list_tasks(self):
        """Удалённо получить все записи Task."""
        return self._call("list_tasks", [])

    def get_task(self, uid):
        """Удалённо получить Task по uid."""
        return self._call("get_task", [uid])

    def create_response(self, row):
        """Удалённо создать Response из списка семи полей."""
        return self._call("create_response", [row])

    def list_responses(self):
        """Удалённо получить все записи Response."""
        return self._call("list_responses", [])

    def get_response(self, uid):
        """Удалённо получить Response по uid."""
        return self._call("get_response", [uid])

    def recent_results(self):
        """Удалённо вычислить проекцию ip, duration, tags за 9 минут."""
        return self._call("recent_results", [])
