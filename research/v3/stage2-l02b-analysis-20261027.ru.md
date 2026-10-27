# L02B: Stage 2 native verdict, 27 октября

**Native FAIL — кандидат не допущен в команду и в рейтинговые матчи.**

Полных корректных ответов: 224/224.
Все шесть первых вызовов превысили1000ms: 1277.3–1843.3ms.
Полный response p50/p95/max: 112.6/164.5/1843.3ms.
Последующие вызовы p50/p95/max: 112.1/137.5/242.4ms.
Invalid responses:0; поздних вызовов:6/224.
Все собственные тестовые сессии закрыты. AWS audit содержит 224
решений точной сборки, modelAttempted=0. Команды и причины сохранены агрегатами
в [L02B native receipt](stage2-native-l02b-initial-20261027.json).

Источник:095e3994b8ea55f6671b7833171c0ff83b484b92; архив:2d0d5c43d10a3ed704b5a30a0543736fa468c1f9a1bb1a52dcc0351dca835375.
Измерение:CloudShell us-east-1, V1, новые session IDs, без прогрева и retries.
Это внешний полный SDK-вызов, не измерение game-server/application latency.
First HTTP и first valid state совпадают в этом синтетическом плане;
first competitive PLAY_ON неизвестен: кандидат не зарегистрирован.

По заранее принятому gate Fitness и серия10 не запускались. WDL, PPG,
GF:GA, shots/SOT, scoreless, clean sheets, HOME/AWAY и игровые late/invalid
остаются null. Не приписывать кандидату контрольные или unbatched матчи.
Тактический эффект не измерен. Сохраняется Baseline; rollback — точные
новые привязки в приватном canonical-bindings.json и свежий Fitness5/5.
