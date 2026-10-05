"""TCP RPC-сервер: один запрос и один ответ на соединение.

Обработчики разделяют один Store. Ошибки входа превращаются в XML-ответ;
ошибка одного клиента не завершает сервер. Запросы и ответы журналируются
вместе с кодами и XML-телом; конфигурация stdout находится в CLI.
"""

import logging
from socketserver import BaseRequestHandler, ThreadingTCPServer

from .codec import decode, encode
from .model import Store
from .operations import NAMES, invoke
from .protocol import ERROR_CODE, TIMEOUT, pack_frame, receive_frame

LOGGER = logging.getLogger("practice23.rpc")


class RpcServer(ThreadingTCPServer):
    """Сервер с общим хранилищем и независимыми потоками клиентов."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, store=None):
        """Привязать сокет; порт 0 позволяет ОС выбрать свободный порт."""
        self.store = Store() if store is None else store
        super().__init__(address, Handler)


class Handler(BaseRequestHandler):
    """Обработчик одного обмена RPC с ограничением времени ожидания."""

    def handle(self):
        """Принять кадр, вызвать модель и отправить результат или ошибку."""
        self.request.settimeout(TIMEOUT)
        code = ERROR_CODE
        try:
            code, body = receive_frame(self.request)
            LOGGER.info("REQUEST code=%s xml=%r", code, body)
            if code not in NAMES:
                raise ValueError("Неизвестный код операции")
            result = invoke(self.server.store, NAMES[code], decode(body))
            payload = ["ok", result]
        except (ValueError, TypeError, OSError) as error:
            LOGGER.info("REQUEST_ERROR code=%s error=%s", code, error)
            payload = ["error", str(error)]
        reply_code = code if code in NAMES else ERROR_CODE
        self._send(reply_code, payload)

    def _send(self, code, payload):
        """Отправить ответ или ошибку превышения размера."""
        try:
            body = encode(payload)
            frame = pack_frame(code, body, reply=True)
        except ValueError as error:
            body = encode(["error", str(error)])
            frame = pack_frame(code, body, reply=True)
        LOGGER.info("RESPONSE code=%s xml=%r", code, body)
        try:
            self.request.sendall(frame)
        except OSError as error:
            LOGGER.info("SEND_ERROR %s", error)
