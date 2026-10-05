"""Единая таблица десяти публичных операций и их кодов на проводе."""

OPERATIONS = (
    "create_member",
    "list_members",
    "get_member",
    "create_task",
    "list_tasks",
    "get_task",
    "create_response",
    "list_responses",
    "get_response",
    "recent_results",
)
CODES = {name: code for code, name in enumerate(OPERATIONS, start=1)}
NAMES = {code: name for name, code in CODES.items()}


def invoke(target, name, args):
    """Вызвать только разрешённую операцию без eval."""
    if name not in CODES:
        raise ValueError("Неизвестная операция")
    if type(args) is not list:
        raise ValueError("args должен быть списком")
    return getattr(target, name)(*args)
