# M11 deep run — итог 26 октября 2026

Статус: offline/deep simulation PASS, AWS native/Fitness/live не выполнены.

Это итог повторной проверки после первоначальной подготовки M11. Первую версию M11 нельзя считать актуальной: deep run обнаружил риски stale tick, неполной binding/identity проверки, противоречивого ownership и более слабого центрального pass gate. Все они изменили дизайн кандидата.

## Финальный дизайн M11 v3

Фиксированная оболочка команды:
- 1-1-2;
- GK13 Nova 2 Lite — без изменений;
- DEF19 Nova 2 Lite — без изменений;
- FWD1v16 Nova 2 Lite — без изменений;
- FWD2 deterministic stance revision9 — без изменений;
- меняется только MID/player2.

MID v3:
1. Сначала проверяет exact binding [2], полный уникальный набор 10 игроков, tick/time/session, unlocked commands и согласованность ownership.
2. Повторный или старый tick не исполняется: CLEAR_OVERRIDE.
3. При собственном владении и во всех неоднозначных состояниях используется проверенная L01 MID policy:
   - прогноз движения соперников по линии паса;
   - receiver clearance;
   - lane clearance;
   - безопасный progressive/recycle pass;
   - близкий открытый удар;
   - при отсутствии безопасного действия release.
4. Только в OPEN_PLAY и явно off-ball управление переходит к FastEngine:
   - support при владении партнёра;
   - один локально ближайший press/intercept;
   - central cover;
   - keep shape.
5. В своей глубокой трети MID не PRESS/INTERCEPT: он MARK/Defend, чтобы не превращаться во второго пресера рядом с DEF.
6. KICK_OFF/RESETTING остаются на L01/default-engine path, чтобы не добавлять ещё одну переменную.
7. Foundation-model calls в MID request path: 0.

## Что deep run нашёл и исправил

### R1 — stale/duplicate tick

Первоначальный FastEngine мог повторно обработать тот же tick. Для FWD2 это неприятно, для MID PASS/SHOOT по старому состоянию опаснее.

Исправление: session freshness gate. Duplicate/out-of-order -> STALE_OR_DUPLICATE_FRAME + CLEAR_OVERRIDE.

### R2 — слишком мягкая binding проверка

FastEngine принимал список myPlayers, если нужный pid просто присутствовал.

Исправление: M11 требует ровно [2], а identities должны быть ровно home/away × agentId_0..4.

### R3 — conflicting ownership

Adversarial case possessionTeamCode=home + possessionTeamId=1 выявил, что исходный FastEngine мог продолжить действие.

Исправление: cross-check isFree, team code/id, agent/player id и hasBall. Противоречие -> release.

### R4 — pass gate FastEngine недостаточен для центрального игрока

FastEngine хорошо подходит ограниченному FWD2, но его current-lane проверка проще L01. L01 учитывает прогнозируемое пересечение линии движущимся соперником.

Исправление: M11 больше не заменяет L01 при владении. On-ball M11 = L01; FastEngine используется только off-ball.

### R5 — возможный DEF + MID double press

DEF19 разрешает press в своей зоне и не содержит столь же жёсткого nearest-player invariant.

Исправление: MID deterministic press не допускается в defensive third. Там MID держит central cover. В middle third остаётся single-nearest press.

### R6 — restart увеличивал поверхность изменения

Pure FastEngine мог выдать PASS на KICK_OFF, тогда как L01 release.

Исправление: restart остаётся L01/default path.

## State / adversarial simulation

CI deep run:
- 6 000 случайных HOME состояний;
- каждое зеркалируется в AWAY;
- M11 и L01 проверяются отдельно;
- дополнительно shadow-прогон FastEngine для пяти ролей;
- adversarial malformed/binding/ownership/session cases.

На финальной политике:
- critical invariant failures: 0;
- M11 safety issues: 0;
- HOME/AWAY type/target mismatches: 0;
- crashes: 0;
- M11 vs L01 mismatch на собственном владении в OPEN_PLAY: 0;
- M11 PRESS/INTERCEPT в defensive third: 0;
- потенциальный deep DEF+MID double press после guard: 0;
- full deterministic shadow multiple pressers: 0;
- unknown-possession active rate: 0%.

В 12 000 M11 HOME/AWAY оценках получены:
- PASS 2 264;
- SHOOT 104;
- MARK 2 572;
- SET_STANCE 3 636;
- PRESS_BALL 50;
- INTERCEPT 28;
- остальные безопасно release.

Это не физическая футбольная симуляция. Она проверяет решение и инварианты, но не доказывает, что pass достигнет адресата или press отберёт мяч.

## Startup / latency deep run

Fresh-process CI сравнение, 12 новых процессов на вариант:
- L02B p50 около 32.8 ms, p95 около 35.0 ms;
- M11 p50 около 33.6 ms, p95 около 35.8 ms;
- разница p50 около +0.85 ms в пользу L02B.

Практический смысл: M11 не имеет значимого локального startup-преимущества перед L02B. Его смысл — off-ball policy/reliability, а не ещё несколько миллисекунд import time.

Главный риск остаётся вне Python:
- L02/V1 fresh-session calls: 1279.7–1340.8 ms, 6/6 выше 1 s;
- later calls p50 95.5 ms / p95 118.0 ms;
- application handler около sub-ms;
- L02B локально уменьшал readiness примерно на 97 ms.

Даже в оптимистичной декомпозиции, где эти примерно 97 ms полностью переносятся на AWS first call, 0/6 исторических first calls пересекли бы 1 s. Для прохода осталось бы убрать примерно ещё 184–283 ms неизвестного внешнего времени.

Следствие: ни L02B, ни M11 нельзя продвигать по локальной скорости. Нужен новый fresh-session native screen.

## Важная гипотеза о bootstrap

В сохранённых real-session аудитах deterministic FWD2 каждая сессия содержит один начальный malformed/bootstrap response. Это допускает гипотезу, что Runtime вызывается технически до полноценного PLAY_ON.

Это не доказательство, что cold call безопасен для соревнования. Поэтому M11 audit теперь сохраняет playMode, gameTime, tick и ordinal. Завтра нужно различать:
- first HTTP call;
- first valid state;
- first competitive PLAY_ON call.

Официальный 1 s deadline не ослабляется по этой гипотезе.

## Почему average latency нельзя использовать как единственный KPI

По 33 сохранённым матчам batches 11–15 с доступной report latency:
- корреляция log(latency) с win около 0.095;
- корреляция с shots-on-target около 0.092;
- <100 ms: 5/7 wins;
- 500–999 ms: 10/11 wins;
- >=1000 ms: 6/10 wins.

Это не доказывает, что latency не важна. Наоборот: report average смешивает разные режимы, fallback/default-engine и не показывает late-command share. Оптимизировать надо timely useful decisions, а не минимальное среднее число в UI.

## Риск пяти матчей

Свежая агрегированная база batches 11–16: 25W / 11L (36 decisive games).

При той же истинной силе 5-матчевый блок очень шумный:
- примерно 5-й percentile: 2 wins;
- median: 4 wins;
- примерно 95-й percentile: 5 wins.

Если кандидат реально лучше baseline на +10 процентных пунктов win rate, вероятность, что он просто выиграет 5-матчевое сравнение, около 50%. Для 10 игр около 60%, для 20 около 71%.

Bayesian screening после пяти игр против этой baseline:
- 2W3L -> около 10% вероятности, что candidate лучше;
- 3W2L -> около 30%;
- 4W1L -> около 60%;
- 5W0L -> около 88%.

Поэтому пять игр = screening, не доказательство.

## Решение для 27 октября

Setup A: L02B, прежний model-free L01 MID + fastboot.

Setup B: M11 v3, тот же L01 on-ball + deterministic OPEN_PLAY off-ball.

Остальные четыре роли и formation не меняются.

Приоритет решения:
1. reliability/native deadline;
2. Fitness;
3. first competitive PLAY_ON latency;
4. timely-useful rate;
5. football outcome / shots on target / scoreless games / goals;
6. только затем raw average latency.

Если кандидат проваливает native, wrong-side/player, ownership, stale tick или Fitness — ranked block не запускается.

Если проходит:
- первые 5 игр — screening;
- 0–2 wins: reject, если нет явной причины качества данных;
- 3W2L: ambiguous, baseline предпочитается; при времени можно ещё 5;
- 4W1L: promising, желательно ещё 5;
- 5W0L: сильный сигнал, но всё ещё не статистическое доказательство; при возможности повторить.
- исчезновение shots-on-target, несколько scoreless игр или central collapse имеют право остановить promotion даже при хорошей latency.

## Что НЕ включать в этот A/B

Не менять одновременно:
- formation;
- GK/DEF/FWD1;
- модель;
- Memory;
- FWD2;
- большой prompt;
- thresholds после старта серии.

Следующая архитектурная гипотеза после M11 — отдельный deterministic/guarded DEF, но не внутри этого эксперимента.
