# M11 Hybrid Fast MID v3

Актуальный live-pilot вариант включает явно согласованный владельцем общий
neutral_restart adapter, такой же как в L02B. На валидном свежем KICK_OFF
с известным ownership и unlocked SET_STANCE он выбирает Balanced; остальные
guards и фазы сохраняют исходный результат. Это универсальное игровое
поведение, не специальная ветка Fitness. Core M11/L01/FastEngine SHA неизменны.

27 октября перед живыми пилотами HTTP entrypoint приведён к поведению
AgentCore SDK: bounded JSON body разбирается независимо от MIME label.
Football Fitness у L02B фактически присылал non-application/json Content-Type,
что прежняя общая транспортная проверка отклоняла415/portal502. Код тактики
M11 v3/L01/FastEngine не менялся. Актуальный SHA — в artifact.json; прежние
native receipts ниже относятся к прежним ZIP, не к этой транспортной сборке.

Статус на 27 октября: **deep simulation PASS; isolated AWS deployment выполнен;
исправленный ZIP native FAIL (6/6 cold calls >1s); в команде не зарегистрирован,
Fitness и ranked M11 не запускались**.

Итог: [Stage 2 comparison](../research/v3/STAGE2_COMPARISON_20261027.ru.md).

Первый CodeZip `d073569c...` не запустился: пакет не включал
`agentic_fc/policy.py`, импортируемый через `agentic_fc/__init__.py`.
AWS native получил timeout, CloudWatch подтвердил ModuleNotFoundError.
Исправление упаковки добавляет этот неизменённый модуль; тактика M11 v3,
FastEngine, L01 и HTTP entrypoint побайтно сохранены.
Новый архив: `b75c11aa2bf592c1b959a77a0b72a71e2d67e839bb8f5e167076b32c1cd8a390`.
Перед новым AWS gate проверять ZIP в изолированных процессах вне репозитория:

    python3 hybrid_fast_v1/verify_local.py

Проверка использует `-I -S` и только извлечённые файлы архива: существующие
модули рабочего checkout больше не могут скрыть пропущенную зависимость.
Локальный PASS по-прежнему не означает native PASS.

Актуальный M11 — не первоначальный pure-FastEngine MID. Deep run 26 октября изменил архитектуру после найденных counterexamples. Полный разбор: research/v3/M11_DEEP_RUN_RESULT_20261026.ru.md.

## Состав кандидата

Formation 1-1-2 неизменна.

- GK13 — текущий M8 / Nova 2 Lite / prompt без изменений.
- DEF19 — текущий M8 / Nova 2 Lite / prompt без изменений.
- MID2 — M11 v3.
- FWD1v16 — текущий M8 / Nova 2 Lite / prompt без изменений.
- FWD2 revision9 — текущий deterministic stance.

Меняется только MID.

## Политика MID v3

M11 не вызывает foundation model.

### С мячом и при неоднозначности

Используется L01 MidEngine. Он остаётся владельцем решений PASS/SHOOT и сохраняет более строгие центральные guardrails:
- прогноз движения соперника;
- проверку receiving space;
- проверку линии паса;
- safe progressive / recycle outlet;
- close clear shot;
- release, если безопасного решения нет.

### Без мяча в OPEN_PLAY

Используется FastEngine:
- при мяче у партнёра — support/stance;
- против соперника — single-nearest local press либо central cover;
- на свободном мяче — bounded intercept;
- unknown possession — release.

Дополнительный hybrid guard запрещает MID становиться вторым пресером в своей defensive third. Там он MARK/Defend.

KICK_OFF/RESETTING не переводятся на FastEngine — это оставляет restart path таким же, как у L01/default engine.

## Безопасность состояния

До футбольного действия M11 проверяет:
- myPlayers должен быть ровно [2];
- полный уникальный набор home/away × agentId_0..4;
- monotonic tick/gameTime внутри session;
- side не может молча измениться в той же session;
- isFree/team code/team id/agent id/player id/hasBall должны быть согласованы;
- malformed unlockedCommands запрещены;
- duplicate/out-of-order frame -> CLEAR_OVERRIDE;
- missing session id -> CLEAR_OVERRIDE.

Session state bounded до 64 записей.

## Deep-run результат

Финальный CI:
- 6 000 random HOME states + 6 000 AWAY mirrors;
- M11 и L01 проверены отдельно;
- adversarial malformed/binding/ownership/session cases;
- full deterministic five-role shadow coordination check.

Итог:
- 0 critical invariant failures;
- 0 safety issues;
- 0 crashes;
- 0 HOME/AWAY target/type mismatches;
- 0 M11-vs-L01 mismatches при собственном владении в OPEN_PLAY;
- 0 MID PRESS/INTERCEPT в defensive third;
- 0 active actions при unknown possession;
- 0 simultaneous pressers в full deterministic shadow.

Это decision simulation, не физический футбольный симулятор.

## Latency: что уже известно

Local fresh-process CI, 12 процессов:
- L02B p50 около 32.8 ms / p95 около 35.0 ms;
- M11 p50 около 33.6 ms / p95 около 35.8 ms.

То есть M11 не выигрывает у L02B локальный startup. Его потенциальная ценность — более полезная off-ball политика при сохранённой L01 on-ball safety.

Главный риск — AWS first-session path. Исторический L02/V1 дал 6/6 first calls 1.28–1.34 s при later p50 около 95.5 ms. Локальное улучшение L02B само по себе не объясняет недостающие 184–283 ms. M11 должен пройти новый native screen; локальный CPU/HTTP PASS его не заменяет.

## Сборка

    python hybrid_fast_v1/build_package.py

Создаёт:
- .local/hybrid-fast-v1/deployment.zip
- hybrid_fast_v1/artifact.json

Архив reproducible, dependency-free. Builder сверяет reviewed FastEngine и L01 policy hashes.

## Изолированный deployment

По умолчанию ничего не меняет:

    python hybrid_fast_v1/deploy.py

После сборки exact commit, на свободной границе серии:

    python hybrid_fast_v1/deploy.py \
      --source-commit <40-char SHA> \
      --bucket <workshop bucket> \
      --execution-role-arn <existing role ARN> \
      --receipt .local/m11/deploy.json \
      --apply

Helper:
- проверяет archive/source hashes;
- пишет private receipt;
- загружает content-addressed ZIP;
- создаёт или явно обновляет только указанный isolated Runtime;
- ждёт READY;
- сверяет artifact/network/lifecycle/env readback.

READY не означает promotion. После него нужен native gate.

## Native screen

Dry run:

    python hybrid_fast_v1/native_probe.py \
      --binding .local/m11/binding.json \
      --output .local/m11/native.json

Реальный collection — только когда матч не идёт:

    python hybrid_fast_v1/native_probe.py \
      --binding .local/m11/binding.json \
      --output .local/m11/native.json \
      --apply

Затем:

    python hybrid_fast_v1/grade_native.py .local/m11/native.json \
      --deadline-ms 1000 \
      --deadline-source "https://agenticfootballcup.com/" \
      --output .local/m11/native-grade.json

Gate не убирает первые вызовы из статистики.

Дополнительно real-session audit должен различать:
- first HTTP call;
- first valid state;
- first PLAY_ON call.

В сохранённых FWD2 sessions встречается один bootstrap/malformed response на сессию, но это только гипотеза о prematch warmup, а не основание ослаблять официальный deadline.

## Протокол Stage 2

A = L02B.
B = M11 v3.

Для каждого:
1. idle/readback;
2. isolated native;
3. только PASS -> exact MID binding;
4. свежий Fitness 5/5;
5. 10 ranked games без изменения setup;
6. checkpoint;
7. rollback MID15 + Fitness перед следующим кандидатом.

Новое указание владельца требует ровно10 завершённых игр на допущенный
неизменный setup. Обе сборки не прошли native, поэтому эти блоки не запускались.
Десять игр были бы свидетельством, не доказательством превосходства.

Главные метрики:
- first competitive PLAY_ON latency;
- late/invalid share;
- p50/p95/max later calls;
- timely-useful decisions;
- goals, shots on target, scoreless games;
- central-cover regressions.

Possession и UI average latency не являются самостоятельными критериями победы.

## Rollback

MID15 текущего M8, остальные роли и 1-1-2 не менять, затем свежий Fitness 5/5.

Если native/Fitness не проходят, M11 ranked block не запускается.
