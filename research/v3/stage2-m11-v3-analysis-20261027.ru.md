# M11 hybrid v3: Stage 2 native verdict, 27 октября

**Native FAIL — кандидат не допущен в команду и в рейтинговые матчи.**

Полных корректных ответов: 30/30.
Все шесть первых вызовов превысили1000ms: 1256.8–1438.6ms.
Полный response p50/p95/max: 112.3/1380.9/1438.6ms.
Последующие вызовы p50/p95/max: 107.9/133.3/139.2ms.
Invalid responses:0; поздних вызовов:6/30.
Все собственные тестовые сессии закрыты. AWS audit содержит 30
решений точной сборки, modelAttempted=0. Команды и причины сохранены агрегатами
в [M11 hybrid v3 native receipt](stage2-native-m11-fixed-20261027.json).

Источник:244065b0d3fe10447759c2afa8684f42fa566474; архив:b75c11aa2bf592c1b959a77a0b72a71e2d67e839bb8f5e167076b32c1cd8a390.
Измерение:CloudShell us-east-1, V1, новые session IDs, без прогрева и retries.
Это внешний полный SDK-вызов, не измерение game-server/application latency.
First HTTP и first valid state совпадают в этом синтетическом плане;
first competitive PLAY_ON неизвестен: кандидат не зарегистрирован.

По заранее принятому gate Fitness и серия10 не запускались. WDL, PPG,
GF:GA, shots/SOT, scoreless, clean sheets, HOME/AWAY и игровые late/invalid
остаются null. Не приписывать кандидату контрольные или unbatched матчи.
Тактический эффект не измерен. Сохраняется Baseline; rollback — точные
новые привязки в приватном canonical-bindings.json и свежий Fitness5/5.

Первый ZIP отдельно провалил запуск: ModuleNotFoundError для agentic_fc.policy.
Исправлена только упаковка; извлечённый ZIP прошёл30/30 в шести изолированных
процессах. Ошибка старого ZIP не смешивается с native нового архива.
