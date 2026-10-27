# L02B: исправление запуска L02 на V1

## Football compatibility correction — 27 октября

Живой Football Fitness выявил отличие от native Python SDK: корректно
фреймированный POST /invocations с JSON body2512 bytes приходит с Content-Type,
отличным от application/json. Строгая MIME-проверка отвечала415, портал
показывал MID runtime502 и Fitness4/5. Диагностические метки подтвердили отказ;
сырые заголовки/тело не сохранялись в публичных данных.

Исправление соответствует установленному AgentCore SDK `_handle_invocation`:
он вызывает `await request.json()` без MIME gate. Транспорт теперь валидирует
ограниченные JSON bytes независимо от MIME label. Дублированные заголовки,
неоднозначный framing, размеры, invalid/truncated JSON остаются отклонёнными.
Политика L01 не меняется. Аналогично исправлен M11 v3 HTTP entrypoint.
Проверки включают отсутствующий MIME, application/octet-stream и text/plain
с полным правильным решением; invalid JSON не превращается в команду.
Это исправление Football compatibility, не заявление native deadline PASS.

Кандидат, не установлен. Native и Fitness ещё не выполнены. Исходный L02
сохранён: его провалы на V1/V2 не отменяются. Владелец разрешил автономную
передачу и выпуск после native PASS и свежего Fitness 5/5 на границе серии.

## Измерение и гипотеза

У L02/V1 первые шесть полных ответов занимали 1279.7–1340.8 мс, последующие
218 — p50 95.526 / p95 118.039 мс. Обработчик занимал около 1 мс;
import/readiness 168–236 мс. Источник оставшегося времени до заголовков
не установлен. Даже устранение всего измеренного запуска не гарантирует 1 с.

L02B убирает импорт `http.server` вместе с неиспользуемыми SSL/email/mimetypes
и reverse DNS при bind. SHA256 для аудита впервые импортируется после полного
ответа. TCP_NODELAY включён, заголовки и готовое тело передаются одной записью.
HTTP поддерживает только нужные endpoints, ограничивает размер строк/заголовков
и тела, отвергает неоднозначный Content-Length/Transfer-Encoding. Это изменение
транспорта; все восемь общих исходных модулей L01 остаются байт-в-байт прежними.
Проверка здоровья начинает работать только после создания реального MidEngine.
Нет преждевременных заголовков, скрытого прогрева или исключения первых вызовов.

Различающий тест: уменьшатся ли native import/ready и первый полный ответ.
Новые BOOT/PING/invocation timestamps на V1 позволяют сопоставить первый
health-check с входом запроса. Они не дают времени создания VM или применения
команды игрой. На V2 возраст процесса после snapshot нельзя так интерпретировать.

Локально macOS/ARM64 Python3.9.6, audit включён, по шесть новых процессов:

| Измерение | L02 | L02B |
|---|---:|---:|
| Готовность процесса p50, мс | 220.175 | 122.859 |
| Готовность процесса p95, мс | 249.837 | 139.292 |
| HTTP p50, мс | 0.520 | 0.457 |
| HTTP p95, мс | 0.683 | 0.622 |
| Корректных ответов | 224/224 | 224/224 |

Это два последовательных локальных прогона, не AWS и не оценка выигрыша.
Сохранены [сравнение](../research/v3/model-prompt-lab/results/mid-l02b-startup-comparison.json)
и [полный локальный результат](../research/v3/model-prompt-lab/results/mid-l02b-local.json).

## Точный пакет и воспроизведение

Archive SHA256: `2d0d5c43d10a3ed704b5a30a0543736fa468c1f9a1bb1a52dcc0351dca835375`.
17,345 байт / 9 файлов; повторная сборка идентична. Manifest: `artifact-b.json`.
Архив остаётся в приватной `.local/mid-fast-v2b/deployment.zip`.

```sh
python3 mid_fast_v2/build_package.py --candidate L02B
python3 -m unittest discover -s tests -p 'test_mid*.py' -v
python3 mid_fast_v2/verify_local.py --candidate L02B
```

Проверки охватывают все 224 решения и точные SSE bytes, параллельные сессии,
health-check при занятом движке, keep-alive, неверные/дублированные заголовки,
усечённое/слишком большое тело и отсутствие раннего ответа вместо решения.
Admission отвергает архив L02 вместо L02B и любой первый вызов >1000 мс.

## Готовый запрос игровому потоку

На свободной границе завершённой пятёрки, после проверки окна workshop:

1. Получить точный переданный commit main, собрать `--candidate L02B`, сверить
   manifest/архив. Не менять общий рабочий checkout во время матча.
2. Обновить только изолированный, НЕ зарегистрированный L02 Runtime либо
   создать отдельный с теми же уже разрешёнными role/bucket. Платформа V1,
   CodeZip/PYTHON_3_13/`main.py`, HTTP/PUBLIC, idle900/maxLifetime28800.
   Environment ровно PLAYER_ID=2, MID_AUDIT=1, BUILD_COMMIT=полный commit.
   Не расширять IAM. Readback READY/platform/archive/env/role/network/lifecycle.
3. Новый приватный binding: region/runtimeId/runtimeArn/buildCommit/platformVersion=V1.
   Без прогрева выполнить весь прежний план: 224 запроса, шесть новых сессий.

```sh
python3 mid_fast_v1/native_probe.py --candidate L02B --binding .local/mid-fast-v2b/binding.json --output .local/mid-fast-v2b/native.json --apply
python3 mid_fast_v1/grade_native.py .local/mid-fast-v2b/native.json --candidate L02B --deadline-ms 1000 --deadline-source https://agenticfootballcup.com/ --output .local/mid-fast-v2b/native-grade.json
```

Ненулевой exit code любого шага запрещает продолжение. У grader 0 означает
native PASS, 1 — FAIL, 2 — ошибка входа/файлов. Требуются 224/224, ноль поздних,
все первые ≤1000 мс, общий p95≤800 мс. Сохранить first/later/header/body,
session diagnostics и cleanup только собственных сессий. Коллекция — не PASS.

4. Если native PASS: сохранить старый MID15 binding, заменить только MID,
   сверить остальные четыре роли/1-1-2, выполнить свежий Fitness 5/5. При FAIL
   восстановить MID15 и Fitness 5/5; никаких рейтинговых игр кандидата.
5. При обоих PASS немедленно начать разрешённую пятёрку. В первой реальной
   игровой сессии подтвердить MID_L02B/buildCommit/policy/player2 и сопоставить
   с binding. Только тогда сообщить владельцу, что новый сетап реально играет.

Если native опять FAIL, не повторять тот же пакет и не переходить к warm-only
допуску. Экспортировать обезличенные первые timings, BOOT/PING/request интервалы.
Если выигрыш импорта не переносится в full wall, дальнейшее уменьшение Python
не имеет подтверждённой пользы: нужен поддерживаемый жизненный цикл игровой
сессии или другой путь доставки. Не обещать <10 мс через публичный AWS invoke.
Rollback после допуска — прежний MID15 и свежий Fitness 5/5; остальные неизменны.

Контракт сервера проверен по [AWS HTTP protocol](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-http-protocol-contract.html)
и [Python CodeZip](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html).
