# Stage 2: сравнение и решение, 27 октября 2026

Оба MID-кандидата не допущены по заранее принятому native deadline gate.
Команда восстановлена в новом Workshop как Baseline по содержимому:
GK13 / DEF19 / MID15 / FWD1v16 equivalents, deterministic FWD2 stance
source931af03, formation1-1-2. В новом аккаунте номера Harness/Runtime версий
создаются заново; проверены точные prompt/model/config hashes и все пять ARN.
Итоговый свежий Fitness5/5, READY TO PLAY, активного матча не наблюдалось.

Ни один рейтинговый матч в этом эксперименте не запускался. Это выполнение
условия «native FAIL → не регистрировать и не играть10», а не неполная серия.
Кандидаты никогда не занимали MID slot; контрольный MID оставался привязан.

## Native evidence

Все замеры сделаны из AWS CloudShell us-east-1 на V1, без прогрева, на новых
session IDs, с полным чтением ответа и без retry. Бюджет1000ms повторно
подтверждён на [официальной странице](https://agenticfootballcup.com/).
Это внешний SDK path, не доказательство точной задержки game server.

| Сборка | Полных корректных | Первые вызовы, ms | Full p50 / p95 / max, ms | Later p95, ms | Late / invalid | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| L02B | 224/224 | 6/6 late, 1277–1843 | 112.6 / 164.5 / 1843.3 | 137.5 | 6/224 / 0 | FAIL |
| M11 v3, ZIP correction | 30/30 | 6/6 late, 1257–1439 | 112.3 / 1380.9 / 1438.6 | 133.3 | 6/30 / 0 | FAIL |
| Control FWD2 restoration check | 20/20 | 2/2 late, 2921–2936 | См. отдельный receipt | См. receipt | 2/20 / 0 | Контракт PASS, deadline FAIL |

В первом M11 ZIP отсутствовал agentic_fc/policy.py. AWS startup завершился
ModuleNotFoundError, единственный invoke получил read timeout через30s.
Это время до ошибки, не completed-response latency. Попытка сохранена
[отдельно](stage2-native-m11-initial-20261027.json).

Исправлена только упаковка: добавлен уже проверенный неизменённый модуль.
Новый ZIP прошёл30/30 HTTP-запросов в шести извлечённых isolated-процессах
с Python `-I -S`;16 M11 tests прошли. Все тактические модули сохранили хеши.
Native исправленного ZIP вновь провалил cold-call deadline, поэтому новых
повторов того же архива и warm-only допуска не было.

| Кандидат | Source commit | ZIP SHA256 |
| --- | --- | --- |
| L02B | 095e3994b8ea55f6671b7833171c0ff83b484b92 | 2d0d5c43d10a3ed704b5a30a0543736fa468c1f9a1bb1a52dcc0351dca835375 |
| M11 v3 corrected package | 244065b0d3fe10447759c2afa8684f42fa566474 | b75c11aa2bf592c1b959a77a0b72a71e2d67e839bb8f5e167076b32c1cd8a390 |

AWS application audit содержит224 L02B и30 M11 решений точных сборок;
modelAttempted=0 во всех. Полные native command/reason distributions,
header/body и application timings сохранены в
[L02B receipt](stage2-native-l02b-initial-20261027.json) и
[M11 receipt](stage2-native-m11-fixed-20261027.json).
Все собственные native-сессии, включая неудачный M11 startup, остановлены.

First HTTP и first valid state совпали в этих синтетических планах. У L02B
первые состояния PLAY_ON, у M11 OPEN_PLAY. First **competitive** PLAY_ON,
применение команд и игровой late rate неизвестны: матчей кандидатов не было.
Размеры native-планов различаются; доля cold calls6/224 и6/30 делает общий
p95/late percentage несопоставимыми как head-to-head football KPI.
M11 native-план также в основном упражнял safe releases/guards; успешной
AWS-проверки всего off-ball поведения этим результатом не заявляем.

## Контрольная история

Последняя законченная контрольная пятёрка, batch21:2W/0D/3L, PPG1.2,
голы9:7, SOT1.8/game, одна scoreless и одна clean sheet.
Последние две контрольные пятёрки:6W/0D/4L, PPG1.8, голы15:10,
69:43 shots,15:10 SOT, одна scoreless и четыре clean sheets.
Последние пять контрольных блоков:18W/1D/6L, PPG2.2, голы35:15;
shots/SOT доступны24/25, стороны подтверждены не для всех игр.

Это Stage 1, другие соперники и прежний Workshop. Unbatched матчи не
добавлялись к контролируемым сериям. Пересчёт и точные Git/hash sources:
[baseline history](stage2-baseline-history-20261027.json). Новых футбольных
данных для сравнения кандидатов с контролем или между собой не получено.

## Decision table

Знак — означает «не измерено / не запускалось», не ноль. WDL и прочая
футбольная статистика в этой таблице относятся к новым Stage 2 сериям.
Late rate — только native sample; у Baseline измерен один FWD2.

| Setup | Native | Fitness | 10-game WDL | PPG | GF:GA | SOT/game | Scoreless | HOME | AWAY | Late rate | Reliability | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline | FWD2 contract20/20; cold FAIL | 5/5 | — | — | — | — | — | — | — | FWD2:2/20 | Fitness PASS; cold-start risk | Keep control |
| L02B | FAIL:6/6 cold late | — | — | — | — | — | — | — | — | 6/224 | 0 invalid; deadline failed | Not admitted |
| M11 V3 corrected ZIP | FAIL:6/6 cold late | — | — | — | — | — | — | — | — | 6/30 | 0 invalid; deadline failed | Not admitted |

**Причина:** ни один кандидат не удовлетворяет обязательному deadline gate.
Уверенность высокая в отказе допуска этих точных сборок в измеренном screen;
низкая в сравнительной футбольной силе — её не измеряли. Нельзя заявлять,
что Baseline оптимален или что исправленный M11 тактически слабее.

Риски: контрольный FWD2 тоже имеет cold-start deadline misses; full-team
competitive latency не подтверждена; bootstrap до матча остаётся гипотезой;
назначение группы G не подтверждено видимым порталом. Fitness и его0ms display
не доказывают соблюдение игрового deadline. FWD2 UI model badges также
сохранили старые подписи; они не заменяют runtime/source audit.

Итоговая таблица не изменилась:#11,198 played,119W/6D/73L,363points,
голы268:162. Дельта эксперимента:0 матчей/очков/голов. Конкуренты могли
двигаться независимо; текущий ранг не выводился из старого checkpoint.

Точный rollback уже зарегистрирован: приватный
`.local/stage2-20261027/canonical-bindings.json`; MID15-equivalent ARN также
в `baseline-restore.json`, deterministic FWD2 — в `fwd2-binding.json`.
При восстановлении проверить все пять привязок, formation1-1-2 и новый
Fitness5/5. Откат/проверка на текущей границе выполнены. IAM не расширялся,
автоматизации и дополнительные агенты не создавались, PR не мержился.

EVIDENCE INSUFFICIENT — KEEP BASELINE
