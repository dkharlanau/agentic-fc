# L02 — облегчённый запуск MID

Статус: локально готов к native, **допуска и Fitness пока нет**. Исправляет
предполагаемые накладные расходы запуска L01, сохраняя всю его футбольную
политику и восемь исходных модулей байт-в-байт. Это новый вариант исполнения
MID без модели, не новая LLM. Остальная команда и 1-1-2 остаются контролем.

## Что установлено

[Native L01](../research/v3/model-prompt-lab/results/mid-l01-native-screen-20261025.json):
224/224 корректных решения, но 6/6 первых вызовов новых сессий просрочены.
Первые p50/p95/max 2865/3409/3418 мс; остальные 218: 106/127/289 мс.
Общий p95 145 мс скрывает проблему: первых вызовов только 2,68% выборки.
Матч EPAM сыгран прежней командой; Fitness L01 не проводился.

Гипотеза: SDK/imports и подготовка CodeZip объясняют часть задержки. Это не
доказательство, что весь избыток времени находится в нашем приложении.
Без серверной трассы неизвестны доли запуска среды AWS, загрузки кода,
Python, импорта и сети. При провале L02 нельзя объявить задачу решённой или
маскировать первый вызов прогревом другой сессии.

AWS выделяет отдельную среду новой сессии, поэтому сохранение тёплого probe
не гарантирует быстрый первый запрос реального матча:
[изоляция сессий](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html).

Игровому оператору передана дополнительная настройка `platformVersion=V2`:
она восстанавливает подготовленный snapshot вместо полной инициализации среды
каждый раз. Это часть исправления запуска, а не тактическая правка. Сравнение
L01/V1 с L02/V2 не отделит эффект упаковки от эффекта платформы. Создание
snapshot занимает несколько минут; `READY` обязателен до native. Гарантии
дедлайна нет: [платформа V2](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html).

## Единственное изменение

Новый `main.py` использует stdlib HTTP, `/ping` и `/invocations`, порт 8080.
SDK, boto3, Pydantic, Starlette и Uvicorn отсутствуют в архиве. Размер
20 613 452 → 16 499 байт, 2733 → 9 файлов. Формат SSE в точности повторяет
L01, включая JSON-строку внутри `data:`; не заменён на простой JSON.
Управление владением и защитой от старых кадров осталось в `MidEngine` L01.
Состояние обновляется под блокировкой, health-check отвечает независимо.

AWS разрешает собственный HTTP-сервер для CodeZip:
[Python direct deployment](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html),
[HTTP contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-http-protocol-contract.html).
Это документальная совместимость; фактическую совместимость подтвердит native/Fitness.

В логах `MID_L02_BOOT` измеряются imports и готовность сервера после старта Python.
В `MID_L02` — decode/очередь/решение/flush, ordinal, хеш входного payload и build.
Сырые данные, координаты и session IDs не логируются. Замеры boot не включают
создание microVM/Python launcher; wall native включает весь запрос. Лог пишется
после отправки ответа. Сопоставлять `payloadSha256` с приватным native receipt.

На V2 **не интерпретировать `processAgeAtHandlerMs` как время cold-start**:
reference до snapshot не измеряет restore. `importMs`/`readyMs` характеризуют
подготовку snapshot, остальные durations внутри запроса остаются пригодны.
Первый full native wall остаётся обязательным внешним измерением.
[Правила измерения после restore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-v2-optimize.html).

## Воспроизведение офлайн

```sh
python3 mid_fast_v2/build_package.py
python3 -m unittest discover -s tests -p 'test_mid*.py' -v
python3 mid_fast_v2/verify_local.py
```

23 проверки прошли. Извлечённый архив стартовал в 6 чистых процессах с
отключёнными site-packages: 224/224 ответа. Локальный macOS ARM64/Python3.9.6:
готовность процесса p50/p95 192/212 мс; HTTP p50/p95 0,48/0,66 мс.
Это **не AWS latency**. Полный результат:
[mid-l02-local.json](../research/v3/model-prompt-lab/results/mid-l02-local.json).
Python3.13/Linux и игровое применение ещё не проверены.

## Передача игровому оператору

Владелец разрешил выпуск после допуска; дополнительное подтверждение не нужно.
Дождаться границы текущей серии, проверить отсутствие активного/входящего матча,
разрешённое окно и приватно сохранить точные текущие bindings/rollback MID15.
Все дальнейшие AWS/портальные действия выполняет один игровой оператор.

1. В отдельном checkout этого точного commit собрать архив командой выше.
   Сверить SHA256 с `mid_fast_v2/artifact.json`. Создать **отдельный** Runtime L02
   по схеме L01: CodeZip/PYTHON_3_13/`main.py`, HTTP, `platformVersion=V2`, существующие role/bucket,
   network PUBLIC, idle900/maxLifetime28800. Environment ровно PLAYER_ID=2,
   MID_AUDIT=1, BUILD_COMMIT=точный commit. IAM не расширять.
2. Readback READY, platformVersion V2, archive, role/network/lifecycle/env. Приватный binding JSON:
   region/runtimeId/runtimeArn/buildCommit, путь `.local/mid-fast-v2/binding.json`.
   До native PASS новая привязка MID не выполняется.
3. Запустить все 224 запроса с шестью НОВЫМИ сессиями. Сохранить первые ответы,
   заголовки/полный body timing, ошибки; остановить только собственные probes.

```sh
python3 mid_fast_v1/native_probe.py --candidate L02 --binding .local/mid-fast-v2/binding.json --output .local/mid-fast-v2/native.json --apply
python3 mid_fast_v1/grade_native.py .local/mid-fast-v2/native.json --candidate L02 --deadline-ms 1000 --deadline-source https://agenticfootballcup.com/ --output .local/mid-fast-v2/native-grade.json
```

Проверить `nativeGatePassed: true` в результате; успешный выход CLI сам по себе
не PASS. Дедлайн 1000 мс подтверждён игровым оператором в receipt L01; перед
выпуском сверить, что правило не изменилось. Требуется 224/224 корректных полных
ответа, ноль просрочек, общий p95≤800 мс. Любой первый ответ >1с — FAIL.
Формат и ожидаемые решения, порядок, plan/archive hashes также обязательны.
Прогрев чужой сессии и исключение первых вызовов не меняют допуск.

4. Только при native PASS заменить MID, сверить остальные четыре bindings,
   выполнить свежий Fitness5/5. Если он не прошёл — вернуть MID15 и Fitness5/5.
5. При PASS начать пять рейтинговых матчей на одном составе. Подтвердить build
   по фактической новой игровой сессии: `MID_L02` + правильный MID + code hash.
   Сообщить владельцу явно: **«MID L02 установлен, native PASS, Fitness5/5;
   первый матч с L02: …»**. До этой цепочки писать «кандидат», не «уже играет».

Если native FAIL: состав сохранить; экспортировать обезличенные
first/later p50/p95/max и 6 первых timings, а приватно headers/full-body и
`MID_L02_BOOT`/`MID_L02` для этих запросов. Вернуть результат исследовательскому
потоку по разрешению владельца. Дальнейшее исправление выбирать по измеренному
этапу, не менять тактику/модель вместе с исправлением транспорта.

Rollback: исходный MID15 и свежий Fitness5/5; точный binding из приватного
readback. Остальные четыре роли и формацию не менять.
