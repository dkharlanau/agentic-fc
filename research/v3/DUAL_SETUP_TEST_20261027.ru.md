# Dual setup test — 27 October 2026

Цель: сравнить два MID-кандидата при одинаковой остальной команде и не перепутать latency improvement с изменением сразу нескольких ролей.

## Fixed team shell

Formation 1-1-2.
GK13 Nova2 Lite unchanged.
DEF19 Nova2 Lite unchanged.
FWD1v16 Nova2 Lite unchanged.
FWD2 deterministic stance revision9 unchanged.

Меняется только MID.

## Candidate A — L02B

Предыдущий кандидат из mid_fast_v2/FASTBOOT.ru.md. Football policy L01, model-free; fastboot transport. Исторический L02/V1 и V2 провалил first-call gate. L02B имеет новый startup hypothesis, но AWS PASS ещё не доказан.

## Candidate B — M11

hybrid_fast_v1. FastEngine stance, player2, model-free, stdlib-only package. Это другая deterministic MID policy и другая минимальная упаковка. До native/Fitness не считать её лучше.

## Order

1. Проверить, что нет live match/probe.
2. Снять baseline role/version/hash snapshot.
3. A isolated native. FAIL -> не Fitness и не ranked.
4. A PASS -> exact binding -> Fitness5/5 -> 5 ranked games -> checkpoint -> rollback.
5. Fresh baseline Fitness5/5.
6. B isolated native. FAIL -> не Fitness и не ranked.
7. B PASS -> exact binding -> Fitness5/5 -> 5 ranked games -> checkpoint -> rollback.
8. Сравнить A/B/baseline только после завершения блоков.

## Same measurement sheet for A and B

Per candidate:
- native plan size and archive hash;
- first-call n/misses, p50/p95/max;
- later-call p50/p95/max;
- incomplete/invalid count;
- Fitness result;
- five games: side/opponent/result/score/shots/shots-on-target/possession/report mean latency;
- exact candidate audit: command counts/reasons/modelCalls;
- leaderboard delta only as context, not causal proof.

## Decision rule

Reject immediately on wrong player, wrong side, invalid command, incomplete response, native deadline failure or Fitness failure.

After five games:
- prefer the candidate with no reliability regression and materially better timely-useful response profile;
- football cannot disappear: no rise in scoreless games or obvious collapse in shots-on-target;
- one large win does not hide the other four games;
- if evidence is mixed, keep baseline rather than combine A+B or alter another role.

Do not test a new formation, model family or prompt rewrite in the same block.
