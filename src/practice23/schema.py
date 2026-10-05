"""Схемы записей и проверка типов без изменения пользовательских данных.

Позиции полей совпадают с рисунком 23. bool проверяется отдельно от int:
в Python isinstance(True, int) истинно, но логическое значение не
является идентификатором или меткой времени в принятом интерфейсе.
"""

SCHEMAS = {
    "member": ("uid datetime ip locale", (int, int, str, str)),
    "task": (
        "uid datetime input member tags completed launched",
        (int, int, str, int, str, int, int),
    ),
    "response": (
        "uid datetime response status failure task duration",
        (int, int, str, str, str, int, int),
    ),
}
REFERENCES = {"task": (3, "member"), "response": (5, "task")}
UID = 0
RESPONSE_TIME = 1
TASK_MEMBER = 3
TASK_TAGS = 4
RESPONSE_TASK = 5
RESPONSE_DURATION = 6
MEMBER_IP = 2
WINDOW_SECONDS = 9 * 60
MIN_UID = 1
MIN_DURATION = 0


def validate_uid(uid):
    """Проверить положительный целый ключ, исключая bool."""
    if type(uid) is not int or uid < MIN_UID:
        raise ValueError("uid должен быть положительным целым числом")


def validate_row(entity, row):
    """Проверить длину и точные типы списка до изменения состояния.

    Имена полей нужны для понятных сообщений. Времена остаются целыми
    числами; дополнительные диапазоны, отсутствующие в задании, не
    вводятся. duration не может быть отрицательной величиной.
    """
    names, types = SCHEMAS[entity]
    if type(row) is not list or len(row) != len(types):
        raise ValueError(f"{entity}: нужен список из {len(types)} полей")
    for name, value, expected in zip(names.split(), row, types):
        if type(value) is not expected:
            raise ValueError(f"{name}: ожидается {expected.__name__}")
    validate_uid(row[UID])
    if entity == "response" and row[RESPONSE_DURATION] < MIN_DURATION:
        raise ValueError("duration не может быть отрицательной")
