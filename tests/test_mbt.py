"""Model-Based Testing реального RPC с независимой моделью-словарём.

Hypothesis генерирует аргументы и последовательности действий. Эталон
не вызывает Store, его валидатор или его выборку. В invariant после
каждого шага сверяются все отношения и реляционная проекция.
"""

import threading

import pytest
from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant
from hypothesis.stateful import rule

from practice23.client import RpcClient, RpcError
from practice23.model import Store
from practice23.server import RpcServer

TEXT = st.text(max_size=15)
UIDS = st.integers(min_value=1, max_value=8)
DELTAS = st.sampled_from([-600, -541, -540, -539, -1, 0, 1, 60])
PLURALS = {"member": "members", "task": "tasks", "response": "responses"}


class RpcMachine(RuleBasedStateMachine):
    """Два состояния получают одни действия: RPC и простой эталон."""

    def __init__(self):
        """Для каждого примера поднять новый пустой сервер и новые часы."""
        super().__init__()
        self.now = 1000
        self.expected = {name: {} for name in PLURALS}
        self.server = RpcServer(
            ("127.0.0.1", 0), Store(clock=lambda: self.now),
        )
        self.worker = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.001},
        )
        self.worker.start()
        self.client = RpcClient(*self.server.server_address)

    def teardown(self):
        """Закрыть сервер даже после найденного Hypothesis контрпримера."""
        self.server.shutdown()
        self.worker.join()
        self.server.server_close()
        super().teardown()

    def create(self, entity, row, valid=True):
        """Независимо решить, разрешена ли вставка, и сверить её результат."""
        table = self.expected[entity]
        accepted = valid and row[0] not in table
        method = getattr(self.client, f"create_{entity}")
        if not accepted:
            with pytest.raises(RpcError):
                method(row)
            return
        assert method(row) == row
        table[row[0]] = row.copy()

    @initialize(
        ip=TEXT, tags=TEXT, duration=st.integers(0, 100),
        invalid_duration=st.integers(-100, -1),
    )
    def seed_relations(self, ip, tags, duration, invalid_duration):
        """Генерируемая начальная цепочка обеспечивает вызов всех 10 методов.

        Два свежих ответа имеют одну проекцию; ещё один лежит точно на
        границе. Поэтому тест ловит потерю DISTINCT и ошибочное >=.
        """
        self.create("member", [1, self.now, ip, "ru"])
        self.create("task", [1, self.now, "", 1, tags, 0, 1])
        for uid, age in [(1, 0), (2, 1), (3, 540)]:
            row = [uid, self.now - age, "", "ok", "", 1, duration]
            self.create("response", row)
        invalid = [4, self.now, "", "ok", "", 1, invalid_duration]
        self.create("response", invalid, valid=False)

    @rule(uid=UIDS, ip=TEXT, locale=TEXT)
    def add_member(self, uid, ip, locale):
        """Проверить уникальные ключи и дубликаты на произвольных строках."""
        self.create("member", [uid, self.now, ip, locale])

    @rule(uid=UIDS, parent=UIDS, text=TEXT, tags=TEXT)
    def add_task(self, uid, parent, text, tags):
        """Проверить создание задачи и наличие участника."""
        row = [uid, self.now, text, parent, tags, 0, 1]
        self.create("task", row, parent in self.expected["member"])

    @rule(uid=UIDS, parent=UIDS, delta=DELTAS, duration=st.integers(-1, 100))
    def add_response(self, uid, parent, delta, duration):
        """Проверить времена ответа и неотрицательность duration."""
        row = [uid, self.now + delta, "<&>", "ok", "", parent, duration]
        valid = parent in self.expected["task"] and duration >= 0
        self.create("response", row, valid)

    @rule(entity=st.sampled_from(tuple(PLURALS)), uid=UIDS)
    def read_one(self, entity, uid):
        """Сверить чтение существующего и отсутствующего идентификатора."""
        method = getattr(self.client, f"get_{entity}")
        if uid in self.expected[entity]:
            assert method(uid) == self.expected[entity][uid]
        else:
            with pytest.raises(RpcError):
                method(uid)

    @rule(seconds=st.integers(0, 600))
    def advance_time(self, seconds):
        """Сдвинуть часы: сохранённые ответы должны постепенно устаревать."""
        self.now += seconds

    @rule(entity=st.sampled_from(tuple(PLURALS)), bad=st.sampled_from([
        [], [0], "not-a-list", [1, "bad", "ip", "ru"],
    ]))
    def malformed_record(self, entity, bad):
        """Неверная длина или тип записи не должны менять состояние."""
        with pytest.raises(RpcError):
            getattr(self.client, f"create_{entity}")(bad)

    @rule(entity=st.sampled_from(tuple(PLURALS)), uid=st.sampled_from([
        0, -1, "1", [], 999,
    ]))
    def invalid_lookup(self, entity, uid):
        """Невалидный или отсутствующий ключ даёт контролируемую RPC-ошибку."""
        with pytest.raises(RpcError):
            getattr(self.client, f"get_{entity}")(uid)

    @invariant()
    def all_relations_match(self):
        """Сверить списки и отдельные записи после каждого шага."""
        for entity, table in self.expected.items():
            rows = [table[uid] for uid in sorted(table)]
            actual = getattr(self.client, f"list_{PLURALS[entity]}")()
            assert actual == rows
            for uid, row in table.items():
                assert getattr(self.client, f"get_{entity}")(uid) == row

    @invariant()
    def projection_matches(self):
        """Эталон — декартово произведение с условиями, без индексов Store."""
        expected = {
            (member[2], response[6], task[4])
            for member in self.expected["member"].values()
            for task in self.expected["task"].values()
            for response in self.expected["response"].values()
            if member[0] == task[3] and task[0] == response[5]
            and response[1] > self.now - 540
        }
        actual = self.client.recent_results()
        assert actual == [list(row) for row in sorted(expected)]


TestRpcMachine = RpcMachine.TestCase
TestRpcMachine.settings = settings(
    max_examples=40, stateful_step_count=35, deadline=None,
    derandomize=True, database=None,
)
