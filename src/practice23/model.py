"""Слой данных в оперативной памяти и десять операций варианта 23.

Каждая запись — обычный list. Словарь служит индексом по uid и не меняет
требуемое представление записи. RLock делает проверку и вставку
атомарными. На входе и выходе создаются копии списков, чтобы вызывающий
код не мог испортить хранилище в обход проверки. Все поля скалярные:
shallow copy достаточно. Данные не записываются на диск.
"""

from threading import RLock
from time import time

from .schema import (
    MEMBER_IP,
    REFERENCES,
    RESPONSE_DURATION,
    RESPONSE_TASK,
    RESPONSE_TIME,
    SCHEMAS,
    TASK_MEMBER,
    TASK_TAGS,
    UID,
    WINDOW_SECONDS,
    validate_row,
    validate_uid,
)


class Store:
    """Хранилище с настраиваемыми часами clock."""

    def __init__(self, clock=time):
        """Создать пустые отношения и сохранить часы."""
        self._tables = {name: {} for name in SCHEMAS}
        self._clock = clock
        self._lock = RLock()

    def _create(self, entity, row):
        """Проверить запись и ключи, затем вставить копию."""
        validate_row(entity, row)
        with self._lock:
            table = self._tables[entity]
            if row[UID] in table:
                raise ValueError(f"{entity}: uid {row[UID]} уже существует")
            if entity in REFERENCES:
                position, parent = REFERENCES[entity]
                if row[position] not in self._tables[parent]:
                    raise ValueError(f"{parent}: внешний ключ не найден")
            table[row[UID]] = row.copy()
            return row.copy()

    def _list(self, entity):
        """Вернуть копии в порядке uid для стабильного отображения и
        тестов.
        """
        with self._lock:
            table = self._tables[entity]
            return [table[uid].copy() for uid in sorted(table)]

    def _get(self, entity, uid):
        """Вернуть копию записи; отсутствие ключа является явной
        ошибкой.
        """
        validate_uid(uid)
        with self._lock:
            if uid not in self._tables[entity]:
                raise ValueError(f"{entity}: uid {uid} не найден")
            return self._tables[entity][uid].copy()

    def create_member(self, row):
        """Создать Member: [uid, datetime, ip, locale]."""
        return self._create("member", row)

    def list_members(self):
        """Прочитать все Member, не раскрывая изменяемые внутренние
        списки.
        """
        return self._list("member")

    def get_member(self, uid):
        """Прочитать один Member по положительному целому uid."""
        return self._get("member", uid)

    def create_task(self, row):
        """Создать Task из семи полей в порядке схемы.

        member должен ссылаться на существующий Member. completed и
        launched сохраняются как int, поскольку именно такой тип указан
        на диаграмме.
        """
        return self._create("task", row)

    def list_tasks(self):
        """Прочитать все задачи по возрастанию uid."""
        return self._list("task")

    def get_task(self, uid):
        """Прочитать задачу или вызвать ValueError."""
        return self._get("task", uid)

    def create_response(self, row):
        """Создать Response с полями uid, datetime, response, status,
        failure, task, duration. task должен существовать; duration
        неотрицательна.
        """
        return self._create("response", row)

    def list_responses(self):
        """Прочитать все ответы, включая старые."""
        return self._list("response")

    def get_response(self, uid):
        """Прочитать отдельный ответ по его uid, а не по uid задачи."""
        return self._get("response", uid)

    def recent_results(self):
        """Вычислить проекцию [Member.ip, Response.duration, Task.tags].

        Перебор начинается с Response: это сохраняемая сторона RIGHT
        JOIN. Отбор использует строгое >; ровно now-540 не проходит.
        Затем INNER JOIN с Member исключает строки без задачи или
        участника. DISTINCT соответствует множественной семантике
        реляционной проекции. Верхней границы времени в задании нет:
        будущие ответы тоже проходят.
        """
        with self._lock:
            cutoff = self._clock() - WINDOW_SECONDS
            result = []
            for response in self._tables["response"].values():
                if response[RESPONSE_TIME] <= cutoff:
                    continue
                row = self._project(response)
                if row not in result:
                    result.append(row)
            return sorted(result)

    def _project(self, response):
        """Выполнить соединения по внешним ключам и оставить три поля.

        Целостность при вставке гарантирует наличие связанных строк.
        Благодаря этому правое соединение не порождает NULL-строк:
        допустимое состояние эквивалентно двум внутренним соединениям.
        """
        task = self._tables["task"][response[RESPONSE_TASK]]
        member = self._tables["member"][task[TASK_MEMBER]]
        return [
            member[MEMBER_IP],
            response[RESPONSE_DURATION],
            task[TASK_TAGS],
        ]
