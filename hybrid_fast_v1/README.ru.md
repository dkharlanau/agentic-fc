# M11 Hybrid Fast MID

Статус: подготовлен в Git, не деплоился, не регистрировался в портале и не играл рейтинговые матчи.

## Зачем нужен второй кандидат

Текущая рабочая база уже имеет model-free FWD2 stance. Четыре остальные роли используют Harness/Nova 2 Lite. История показала две независимые проблемы: модель может занимать сотни миллисекунд, но первый вызов model-free Runtime тоже может занимать секунды. Поэтому M11 не добавляет новый длинный prompt. Он убирает LLM только у MID и одновременно упаковывает уже проверенную FastEngine policy в маленький stdlib-only CodeZip.

Состав M11:
- GK13 — текущий M8, Nova 2 Lite, prompt без изменений.
- DEF19 — текущий M8, Nova 2 Lite, prompt без изменений.
- MID2 — M11 model-free FastEngine stance.
- FWD1v16 — текущий M8, Nova 2 Lite, prompt без изменений.
- FWD2 revision9 — текущий deterministic stance.
- Formation — 1-1-2.

То есть новая идея намеренно не меняет formation, GK, DEF, FWD1 и FWD2. У MID нет prompt вообще.

## Чем M11 отличается от предыдущего L02B

Setup A, L02B: model-free MID на отдельной L01 policy и fastboot transport.

Setup B, M11: model-free MID на общей FastEngine stance policy, которая уже использовалась для deterministic FWD2, плюс минимальный пакет без AgentCore SDK и без внешних Python dependencies.

Оба кандидата уменьшают число LLM-equipped roles с четырёх до трёх. Сравнение должно показать не только latency, но и насколько разные deterministic MID policies сохраняют атаку и центр.

## Офлайн-проверка

Запустить:

    python -m unittest tests.test_hybrid_fast_v1 -v
    python hybrid_fast_v1/build_package.py
    python hybrid_fast_v1/native_probe.py --binding .local/m11/binding.json --output .local/m11/native.json

Последняя команда без --apply только печатает размер и hash плана и не вызывает AWS.

Build создаёт .local/hybrid-fast-v1/deployment.zip и hybrid_fast_v1/artifact.json. Архив обязан оставаться под .local. Builder сверяет reviewed source hashes FastEngine и его зависимостей с fast_path_v2/artifact.json.

## Native gate

Только на свободной границе серии и только в изолированном Runtime, который ещё не зарегистрирован как MID команды:

1. Собрать archive на точном commit.
2. Создать/обновить изолированный Runtime с PYTHON_3_13, entryPoint main.py, PUBLIC network и env:
   PLAYER_ID=2
   M11_MODE=stance
   M11_AUDIT=1
   BUILD_COMMIT=<exact commit>
3. Сохранить private binding под .local: region, runtimeId, runtimeArn, buildCommit.
4. Запустить native_probe.py с --apply.
5. Запустить grade_native.py с тем же подтверждённым deadline и source, что используется для L02B.

Пример формы команды:

    python hybrid_fast_v1/grade_native.py .local/m11/native.json --deadline-ms 1000 --deadline-source "<verified source>" --output .local/m11/native-grade.json

Нельзя подставлять выдуманный source. Если дедлайн не подтверждён, кандидат не продвигается.

Gate:
- полный ordered plan;
- 0 decision mismatch;
- 0 incomplete/failed response;
- каждый первый вызов новой сессии внутри подтверждённого deadline;
- общий p95 <= min(800 ms, 80% deadline);
- owned probe sessions остановлены.

CPU compute и локальный HTTP не считаются end-to-end latency.

## Завтрашний A/B

Сначала текущий baseline остаётся recovery point.

A. L02B:
- isolated native;
- если PASS — заменить только MID;
- свежий Fitness 5/5;
- пять рейтинговых матчей без правок;
- сохранить HOME/AWAY, соперника, счёт, shots/on-target, possession, report latency, late-call evidence;
- вернуть baseline MID15 и Fitness 5/5.

B. M11:
- те же шаги и те же метрики;
- пять рейтинговых матчей одной неизменной конфигурацией;
- после блока вернуть baseline, если M11 не выигрывает одновременно по reliability и football outcome.

Не запускать B, пока A-матч или probe активен, и наоборот.

## Что считать улучшением

Latency:
- first-call miss rate;
- full-response p50/p95/max;
- доля ответов после deadline;
- отдельно first vs later calls.

Football:
- points/game и W/D/L;
- goals for/against;
- shots on target;
- scoreless games;
- потери структуры при переходе;
- не использовать possession как самостоятельный KPI.

M11 не принимается, если он быстрее, но подавляет атаку, ухудшает центр или даёт неправильную HOME/AWAY команду.

## Rollback

Точный rollback — MID15 из current M8, остальные роли и 1-1-2 не трогать, затем свежий Fitness 5/5. Не делать force/reset и не менять другие роли одновременно.

## Почему здесь нет новых prompts

Это сознательное решение. История проекта уже показала, что более длинная инструкция может увеличивать фактический контекст, а более короткий prompt сам по себе не устраняет multi-second first-call/runtime latency. M11 проверяет более сильную гипотезу: простые футбольные решения MID должны исполняться кодом, а не текстовым рассуждением модели.
