# Практическая работа 1 Вариант 23

**Сысоев Даниил Денисович · ИКБО-71-24**  
Прикладная разработка серверных частей веб-приложений на языке Питон.  
Преподаватель: Горчаков Артём Владимирович. РТУ МИРЭА, 2026.

Публичный репозиторий: [python-practice-1-variant-23](https://github.com/iwannasome/python-practice-1-variant-23).

## Этап 1

Записи Member, Task и Response представлены списками в памяти.
Есть создание, чтение всех записей, чтение по uid и общая выборка за 9 минут.
Удаление и изменение не входят в вариант 23.

Запуск модели: `./run.sh model`. Список команд: `help`. Выход: `quit`.

```json
{"method":"create_member","args":[[1,1000,"127.0.0.1","ru"]]}
{"method":"list_members","args":[]}
{"method":"get_member","args":[1]}
```

Подготовка: Python 3.11+, `python3 -m venv .venv`,
`.venv/bin/python -m pip install -e '.[test]'`.
Тесты: `.venv/bin/python -m pytest`.

## Этап 2

`./run.sh server` запускает TCP-сервер, `./run.sh client` — клиентский REPL.
`./run.sh demo` самостоятельно запускает временный сервер и демонстрирует
10 методов и 5 ошибок. Запросы и ответы журнала выводятся в stdout.
Параметры адреса: `--host 127.0.0.1 --port 8023`.

Запрос: версия (1 байт), операция (2), длина XML (4), XML.
Ответ: версия (1 байт), операция (1), длина XML (5), XML.
Все числа заголовка unsigned big-endian. Версия 1; коды 1–10.
Неизвестная операция возвращает ответ с кодом 0. Лимит XML — 1 MiB,
тайм-аут — 3 секунды. Одно соединение обслуживает один вызов.

XML использует элементы list, int, str. Содержимое str — base64 от UTF-8
с surrogatepass, чтобы сохранять любые Python-строки, включая символы,
которые нельзя непосредственно записать в XML 1.0.
Запрос содержит список аргументов, ответ — ["ok", результат] либо
["error", сообщение]. DTD и внешние XML-сущности запрещены.

## Этап 3 и проверка

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pycodestyle src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/python tests/audit_project.py
.venv/bin/python -m coverage erase
.venv/bin/python -m coverage run --branch -m pytest tests/test_mbt.py -q
.venv/bin/python -m coverage report
.venv/bin/python -m coverage html
.venv/bin/python -m coverage json -o coverage.json
.venv/bin/python tests/check_mbt_coverage.py coverage.json
```

В **отдельном MBT-запуске** запускается только RuleBasedStateMachine:
обычные тесты не добавляют покрытие. 40 генерируемых примеров, до 35 действий
в каждом, проверки инвариантов после действий. Это параметры генерации,
а не утверждение о ровно 1400 выполненных шагах. `derandomize=True` делает
прогон воспроизводимым при неизменных версиях и исходниках.

Покрытие всех 10 операций подтверждается автоматически. Модель и проверка
схемы получили 100% строк и ветвей. Общий процент проекта ниже, поскольку
MBT через клиент не запускает консольный интерфейс и все защитные ветви
транспортного слоя. Полный отчёт показывает непокрытые строки, ничего
не исключено из измерения. Дополнительные тесты проверяют испорченный XML,
неправильную версию, размер кадра, фрагментацию, EOF и конкурентную вставку.

Стиль проверяется pycodestyle и Ruff: строки кода до 79 символов,
документация до 72 символов, отступы в 4 пробела и упорядоченные импорты.
В pycodestyle отключено только устаревшее W503: PEP 8 допускает перенос
перед бинарным оператором. GitHub Actions повторяет проверки и тесты
при каждом push и pull request.

## Интерфейс модели и клиента

| Код | Метод | Аргументы | Результат |
|---|---|---|---|
| 1 | create_member | row: list из 4 полей | копия созданной записи |
| 2 | list_members | нет | список записей Member |
| 3 | get_member | uid: int | одна запись Member |
| 4 | create_task | row: list из 7 полей | копия созданной записи |
| 5 | list_tasks | нет | список записей Task |
| 6 | get_task | uid: int | одна запись Task |
| 7 | create_response | row: list из 7 полей | копия созданной записи |
| 8 | list_responses | нет | список записей Response |
| 9 | get_response | uid: int | одна запись Response |
| 10 | recent_results | нет | список [ip, duration, tags] |

| Сущность | Поля списка по порядку |
|---|---|
| Member | uid:int, datetime:int, ip:str, locale:str |
| Task | uid:int, datetime:int, input:str, member:int, tags:str, completed:int, launched:int |
| Response | uid:int, datetime:int, response:str, status:str, failure:str, task:int, duration:int |

UID задаёт вызывающая сторона: положительное целое, уникальное в таблице.
Внешний ключ обязательно ссылается на существующую запись. Ошибки:
дубликат, отсутствующий ключ, неверный тип/длина, отрицательная duration.
Локально это ValueError; удалённо RpcError (подкласс ValueError).
Сетевые ошибки остаются OSError/TimeoutError.

`datetime` трактуется как целая Unix-метка в секундах. Часы сервера используют
`time.time()`; фильтр строго `response.datetime > now - 540`. Ровно 540 секунд
назад не проходит. Ограничения `datetime <= now` в формуле нет: будущее проходит.
`duration` — неотрицательное целое; единица измерения в задании не указана.
`completed` и `launched` — int, без самовольного ограничения значениями 0/1.
IP и locale сохраняются строками: формат IPv4, IPv6 или локали не навязывается.
Проекция удаляет дубликаты; результат сортируется для воспроизводимости.

## Структура и подробные объяснения

- `src/practice23/model.py` — списки, индексы, 10 операций и соединения.
- `schema.py` — поля, константы, проверки типов и значений.
- `operations.py` — единый список разрешённых методов и их кодов.
- `codec.py` — типизированное XML и обратимое представление строк.
- `protocol.py` — заголовки, длины в байтах и чтение потока TCP.
- `server.py` — обработчик запросов, общий Store и журналирование.
- `client.py` — 10 явных методов клиента, совпадающих с методами Store.
- `repl.py`, `demo.py`, `__main__.py` — консоль и демонстрация.
- `tests/test_mbt.py` — независимый эталон и генерируемые сценарии.
- [Подробный разбор кода](docs/code_explained.md) — алгоритмы, причины решений,
  примеры байтов, ошибки, порядок чтения и вопросы для защиты.
- [Соответствие заданию](docs/requirements.md) — проверка каждого требования.

В исходниках объяснения оформлены docstring: обычные комментарии `#`
запрещены правилом П1 сборника. Вспомогательные функции описаны в docstring
рядом с реализацией; README описывает пользовательские операции и настройки.

## Установка с нуля и перенос

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
./run.sh demo
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pip install --no-deps -e .
.\run.bat demo
```

Linux-проверки выполнены на Python 3.14.5. Требуемая версия — Python 3.11+.
Windows-скрипт включён для переноса; фактический запуск Windows не проверялся.
Для shell-скрипта можно задать `PYTHON=/полный/путь/python`.
У RpcClient доступны `host`, `port`, `timeout`; у Store — `clock`.
Остальные параметры: `VERSION`, `MAX_BODY`, `TIMEOUT` в protocol.py,
`MAX_DEPTH=32` в codec.py, `WINDOW_SECONDS=540` в schema.py.

Отдельной компиляции для запуска Python не требуется. Проверка синтаксиса:
`.venv/bin/python -m compileall -q src`. Для построения wheel:
`.venv/bin/python -m pip wheel --no-deps --wheel-dir dist .`.
`dist/`, кеши, виртуальное окружение, отчёты coverage и бинарные файлы
исключены из git. PDF/DOCX и архив выдаются отдельно от исходного репозитория.

## Демонстрация и сдача

В первом терминале: `./run.sh server`, во втором: `./run.sh client`.
Введите `help`, затем команды из `demo_commands()` или используйте
`./run.sh demo`, где сервер поднимается автоматически на свободном порту.
Каждый запуск сервера начинает с пустых таблиц; данные живут только в памяти.
Журнал stdout не является сохранением таблиц на диск.

Этапы сохранены раздельными Conventional Commits. Репозиторий открыт
на GitHub по ссылке в начале README. В СДО передаются эта ссылка и PDF
данного README. PDF, DOCX, ZIP, .venv и кеши не включаются в git.

## Источники

1. Сборник задания №1 ИКБО-71-24: с. 4–5 и 72–74, рисунок и таблица 23.
2. [Python socket](https://docs.python.org/3/library/socket.html).
3. [Hypothesis Stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html).
4. [coverage.py Branch coverage](https://coverage.readthedocs.io/en/7.16.2/branch.html).
