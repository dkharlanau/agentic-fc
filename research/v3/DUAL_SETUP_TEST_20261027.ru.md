# Dual setup test — 27 October 2026

Цель: сравнить два MID-кандидата при одной и той же остальной команде и не спутать football effect, latency effect и случайность соперников.

## Fixed shell

Formation 1-1-2.
GK13 Nova2 Lite unchanged.
DEF19 Nova2 Lite unchanged.
FWD1v16 Nova2 Lite unchanged.
FWD2 deterministic stance revision9 unchanged.

Меняется только MID.

## Candidate A — L02B

Предыдущий кандидат:
- model-free L01 MID policy;
- stdlib fastboot transport;
- on-ball safe pass/shot;
- off-ball в основном release/default engine.

L02B локально уменьшил startup относительно L02, но AWS native PASS пока не доказан.

## Candidate B — M11 v3

Новый deep-run кандидат:
- тот же L01 on-ball path, что A;
- deterministic FastEngine только при явно off-ball OPEN_PLAY;
- no MID press/intercept в own defensive third;
- stale/duplicate tick, exact binding, identity и ownership guards;
- model calls = 0;
- restarts сохраняют L01/default path.

Такой дизайн делает A/B интерпретируемым: основная футбольная разница — активная deterministic off-ball работа MID, а не новый on-ball pass algorithm.

## Gate 0 — перед любым кандидатом

1. Убедиться, что нет LIVE/PREPARING матча и параллельного probe.
2. Сохранить current portal role/version/formation snapshot.
3. Сохранить exact baseline rollback MID15.
4. Проверить workshop/quota.
5. Не менять GK/DEF/FWD1/FWD2/formation.

## Gate 1 — build/readback

Для каждого кандидата отдельный content-addressed archive и private receipt.

Runtime обязан:
- player2 only;
- exact source commit;
- exact archive hash;
- PYTHON_3_13;
- expected network/lifecycle/env;
- READY readback.

READY не является latency PASS.

## Gate 2 — native latency

Fresh sessions. Не скрывать first call хорошим warm p95.

Собирать:
- first HTTP call;
- first valid-state call;
- later calls;
- complete-response p50/p95/max;
- invalid/incomplete;
- session continuity.

Официальный deadline: 1000 ms. Native gate остаётся строгим.

Дополнительная диагностическая гипотеза: в прошлых real FWD2 sessions был один bootstrap/malformed response на сессию. Если завтра реальные логи подтверждают prematch bootstrap, отдельно показать first competitive PLAY_ON. Не подменять им официальный native result и не делать вид, что cold miss исчез.

FAIL native -> не регистрировать кандидата и не запускать ranked block.

## Gate 3 — Fitness

Только после native PASS:
- заменить только MID;
- exact binding/readback;
- fresh Fitness 5/5.

Любой wrong player/side, invalid command, stale repeat, ownership contradiction или Fitness fail -> immediate rollback.

## Gate 4 — ranked screening

Первый блок — 5 завершённых матчей на неизменной конфигурации.

На игру:
- HOME/AWAY;
- opponent;
- score;
- shots / shots on target;
- possession как context, не KPI;
- report mean latency;
- exact candidate command/reason distribution, если доступно;
- first competitive PLAY_ON / late evidence;
- critical reliability signal.

Никаких prompt/model/threshold/formation изменений внутри блока.

## Как трактовать 5 матчей

По baseline batches11–16: 25W/11L. Пять игр имеют высокую дисперсию.

Deep-run screening estimate:
- 2W3L -> примерно 10% posterior chance candidate сильнее baseline;
- 3W2L -> примерно 30%;
- 4W1L -> примерно 60%;
- 5W0L -> примерно 88%.

Даже настоящий +10 percentage-point candidate лишь примерно в половине случаев явно выигрывает 5-game comparison.

Поэтому:
- 0–2 wins: reject, если нет подтверждённой data-quality проблемы;
- 3W2L: ambiguous; baseline предпочтительнее, либо ещё 5 игр;
- 4W1L: promising; ещё 5 игр желательно;
- 5W0L: сильный screening signal, но при наличии окна всё равно повторить.

Если кандидат быстрее, но даёт scoreless/zero-SOT collapse или разрушает central cover — не продвигать.

## Порядок A/B

A:
1. isolated native;
2. PASS -> Fitness5/5;
3. 5 games;
4. сохранить результат;
5. rollback MID15 + fresh Fitness.

B:
1. isolated native;
2. PASS -> Fitness5/5;
3. 5 games;
4. сохранить результат;
5. rollback или promotion decision.

Если A не проходит native, не тратить пять матчей только ради сравнения.
Если B не проходит native, baseline остаётся безопасным ответом.

## Decision hierarchy

1. correct identity/side/state;
2. deadline/reliability;
3. Fitness;
4. timely-useful action rate;
5. no football regression;
6. score/points screening;
7. UI average latency — только diagnostic context.

## Запрещённые смешивания

В эти блоки не добавлять:
- 1-2-1;
- новую foundation model;
- Memory;
- новый FWD1;
- deterministic DEF;
- новый GK;
- большой counterattack prompt;
- thresholds, подобранные после первых результатов.

Следующий эксперимент выбирается после A/B, а не во время него.
