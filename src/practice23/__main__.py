"""CLI для локального REPL, TCP-сервера, клиентского REPL и
демонстрации.
"""

import argparse
import logging
import sys
import threading

from .client import RpcClient
from .demo import demonstrate
from .model import Store
from .repl import run_repl
from .server import RpcServer


def run_demo():
    """Запустить временный сервер с освобождением сокета."""
    with RpcServer(("127.0.0.1", 0)) as server:
        worker = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.01},
        )
        worker.start()
        try:
            demonstrate(RpcClient(*server.server_address))
        finally:
            server.shutdown()
            worker.join()


def main():
    """Разобрать режим запуска и направить журнал RPC в stdout."""
    parser = argparse.ArgumentParser(description="Практика 1, вариант 23")
    parser.add_argument("mode", choices=["model", "server", "client", "demo"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8023)
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(levelname)s %(message)s",
    )
    if args.mode == "model":
        run_repl(Store())
    elif args.mode == "client":
        run_repl(RpcClient(args.host, args.port))
    elif args.mode == "demo":
        run_demo()
    else:
        with RpcServer((args.host, args.port)) as server:
            print(f"RPC слушает {server.server_address}", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("Сервер остановлен")


if __name__ == "__main__":
    main()
