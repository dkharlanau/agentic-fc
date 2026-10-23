# Живые эксперименты — 23 октября 2026

## H2 → H2.1

H2 установлен через AWS Console в пяти существующих Harness. Модель Nova 2 Lite сохранена; temperature 0, maxTokens 256. Исходные версии сохранены в AWS, приватные снимки — вне отслеживания Git.

Fitness H2 дважды: GK/FWD2 PASS, DEF/MID/FWD1 FAIL. Сообщения: 0/1 активных команд и отсутствие команд PASS у команды. Это не ошибка транспорта. H2.1 разрешает активное позиционирование при UNKNOWN и распознаёт явное описание владельца в текстовом состоянии. Повторный Fitness сохранил замечания; причина пока не установлена.

## Первый живой матч H2.1

No Human in the Loop (AWAY) против No Context FC: поражение 1:2 в дополнительное время. Удары 4:11, в створ 1:2, владение 35%:65%.

Наши команды: 492, средняя задержка 1327 мс. MOVE 298; GK_DISTRIBUTE 49; INTERCEPT 38; PRESS 31; SHOOT 30; PASS 29; CLEAR 17. По всем пяти позициям отчёт показывает Success 100%; это не доказывает правильность и применение каждой команды. Средние задержки GK/DEF/MID/FWD1/FWD2: 949/1608/1413/942/1317 мс.

Соперник: 9 команд CLEAR_OVERRIDE, средняя задержка 1 мс. Встроенный AI продолжает играть между командами. Сложность и число команд не гарантируют результат.

AI OVERVIEW содержит причинные догадки и некорректную формулировку про владение. Использовать числовую таблицу, не принимать объяснения генератора за установленную причину.

## Следующие гипотезы

1. Сократить время ответа и число вмешательств MOVE_TO, не отменяя полезное встроенное поведение.
2. Исследовать фактический вход и выход через Observability. Tracing DEF был выключен; включён через консоль после первого матча. Наличие содержательных spans ещё не подтверждено.
3. Сравнить компактную оборону с быстрым выходом и текущий позиционный контракт против живых команд. Модель менять отдельным экспериментом.
4. Memory и Gateway проверять отдельно: сначала доступность, сессионную изоляцию и задержку, затем результат матчей. Наличие функций в интерфейсе не означает их подключения.

Один матч не устанавливает улучшение. В старой истории против того же имени было 0:4, но версии соперника/условия не контролировались.

## H3 Compact Transition — installed, match result pending

Prompts: compact/. GK/DEF/MID/FWD1/FWD2 versions 4/4/6/5/5; all Ready. Nova 2 Lite, temperature 0 and maxTokens 256 retained. This bundle changes both instructions length and tactics; a result cannot be attributed to length alone. Fitness started after deployment.

Advanced features: DEF tracing enabled; GenAI Observability dashboard returns a permissions error, so displayed zeros do not establish no invocations. Workshop confirms Memory support on existing Harness with shared STM resource and distinct actor IDs, scoped by session; not attached yet.

## Fitness diagnosis: built-in tools

Control: restore original DEF/MID/FWD1 prompts, leaving model/settings unchanged. Fitness still 2/5, same roles failed. Direct DEF playground test with explicit possession returned PASS surrounded by prose after File Operations and Shell calls; H3 override also called tools and added prose. Advanced configurations revealed Allowed tools = ["*"], permitting built-in shell/file_operations despite Tools(0). Removing * produced the explicit UI warning: no tools allowed at runtime. Began applying empty allowlist. This is an observed source of extra tool calls in synthetic tests, but not an established cause of Fitness failure. The original A0 configuration also used this allowlist; Fitness recovery remains to be verified.

## Subsequent live match and unresolved Fitness

Dinamo Minsk (HOME) 0:2 No Human in the Loop (AWAY). Shots 5:5, on target 0:2, possession 49:51. Our 24 commands: MOVE 12, PASS 7, PRESS 5; average 13940 ms. Per-role mean GK/DEF/MID/FWD1/FWD2: 17719/15355/12752/12431/11443 ms, reported Success 100%. Opponent 0 commands. Victory does not establish improved tactics; measured latency regressed substantially. No SHOOT commands despite 2 goals reinforces the role of built-in engine behaviour.

Fitness remained 2/5 after original prompts, empty tool allowlists, strict nonempty JSON, DEF maxTokens=1024, and DEF Haiku 4.5 trial. None established a fix. Direct synthetic JSON scenario produced valid PASS; a natural-language-only scenario produced []. These are not the actual Fitness payload.

Creating an isolated custom endpoint was explicitly denied by workshop SCP; no endpoint created. Registering existing DEFAULT endpoint ARN caused INVOCATION_ERROR and was reverted to original base Harness ARN. Portal model metadata updated after Fitness, so initial stale label did not prove stale invocation/session.

DEF APPLICATION_LOGS delivery was configured to the standard same-account vendedlogs group; group exists but no streams observed yet. GenAI dashboard permission failure prevents full trace diagnosis.

Final deployed configuration before final control: H3 strict prompts in compact/; Nova 2 Lite on all five; temperature 0 and maxTokens 256; empty allowed-tools lists; no Memory/Gateway. Versions GK/DEF/MID/FWD1/FWD2 = 6/10/9/8/7. DEF tracing and APPLICATION_LOGS enabled. Full H2.1 rollback was considered but not performed. Root cause of Fitness remains unproven.

## Full A0 control and configuration history

The user's observation was that Fitness worked before the changes. Earlier prompt-only rollback retained temperature=0/maxTokens=256 and therefore was not a full baseline control.

All original prompts are archived in `a0/`. A0 uses Nova 2 Lite, unset inference configuration and Allowed tools `*`, with no Memory/Gateway. The five original prompts include the tactics already present at session start; “A0” does not mean an untouched workshop template.

AWS Console does not save a panel with all inference fields cleared: its Save button becomes disabled. Simply clearing the fields and saving the Harness retained the old parameters. Switching the unsaved model-source selection away from Bedrock and back reset the inference configuration. Saved version inspection then confirmed `Inference configs -`, Nova 2 Lite, and All tools (*). No alternative model source or credentials were saved.

Public-safe setup manifests and prompt hashes: `setups.json`. Live report metrics: `matches.json`. Raw AWS identifiers, account information, credentials, screenshots and traces remain private under ignored `.local/`.

Full A0 restoration was verified in immutable saved version views for all five roles: Nova 2 Lite, no inference config, All tools (*). Fitness still returned 2/5 (GK/FWD2 PASS; DEF/MID/FWD1 FAIL). DEF reported 0/1 active ticks and missing team PASS. This rules out prompt-only rollback as a sufficient remedy, but does not identify the underlying cause. Next isolated diagnostic: one fixed PASS response on DEF.
