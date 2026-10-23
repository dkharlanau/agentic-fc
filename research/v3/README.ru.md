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

## Native Harness response and session diagnostic

A fixed PASS array on DEF produced the exact valid JSON in a new Playground session (reported model latency 595 ms), while Fitness still returned 2/5. A fixed `{"commands":[...]}` envelope also left Fitness at 2/5. Neither diagnostic is a playing strategy; DEF was restored to A0 afterwards.

The Harness dashboard route returned a permissions error, but the actual managed Runtime's **View dashboard** route works. Its OTEL sessions expose a persistent scrimmage session reused by repeated Fitness runs. Recent traces contain only two `AgentCore.Harness.Invoke` spans, HTTP 200, zero model tokens, no model-generation spans. An older call in that session includes model input/output. The initial captured request contains a nested JSON-string `prompt` holding gameState/teamId/myPlayers. These observations motivate a repeated-session/replay hypothesis; the exact cache mechanism is not yet proven.

The observed DEF scrimmage session was stopped with the Console's ordinary “Stop current session and create new session” action; success was confirmed. Fitness still failed. Next control: reload the Player Portal and rerun Fitness from its fresh page state. No endpoint permissions or IAM policies were changed.

After restoring DEF A0, stopping its observed scrimmage session and reloading the portal, Fitness improved to **3/5**, with DEF now PASS. This is the first verified change in the Fitness outcome. The exact contribution of session termination versus fresh portal state is not isolated yet. MID and FWD1 scrimmage session identifiers were separately observed in Runtime OTEL tables and stopped through the same ordinary Console operation; their results are pending.

Stopping the separately observed MID/FWD1 scrimmage sessions, reloading the portal and rerunning Fitness yielded **4/5**: FWD1 now PASS, MID now **NO_PARSE** instead of the previous stale 0/1-active-command result. Its new tip says it responded once but the response was not valid JSON with a commandType field. This is materially different evidence. Next isolated change: retain MID's A0 prompt/model/unset inference, remove its allowed-tools wildcard, stop that Fitness session and rerun from a reloaded portal. Earlier prompt/model/tool trials that reused the old scrimmage session cannot establish that those candidates fail on a fresh invocation.

## Verified Fitness recovery: A0-M1 — 5/5

After retaining MID's A0 prompt/model/unset inference, removing only MID's tool wildcard, stopping its observed scrimmage session and reloading the portal, Fitness displayed **All agents passed. Ready to play.** All five positions PASS; Practice and Find opponent enabled. It reported 5 commands and 100% active. Its displayed 0 ms is not evidence of real model latency.

The reproducible working setup is **A0-M1** in `setups.json`: all five A0 prompts, Nova 2 Lite, inference config unset; Allowed tools `*` for GK/DEF/FWD1/FWD2, empty list for MID; no Memory/Gateway; formation 2-0-2. This is a verified connectivity/format/activity gate, not a proven winning policy.

Recovery required eliminating stale/repeated scrimmage-session effects before evaluating current configurations, then addressing a fresh MID NO_PARSE result. Session reset plus portal reload changed DEF/FWD1 results, and restricting MID tools was followed by its PASS. The exact internal cache mechanism and the individual contribution of reset versus reload are not proven. Earlier same-session candidate failures must not be treated as fresh model comparisons.

The first user-initiated live match after 5/5 was launched via Find opponent. Numeric match results will be appended after View Report.

## Live-03 after recovery: A0-M1 2:1 DarkHorse_AI

First user-initiated live match after 5/5 ended in a 2:1 home win. Shots 6:5, on target 2:1, possession 33%:67%. Our 327 commands averaged 872 ms; per-role GK/DEF/MID/FWD1/FWD2: 601/599/796/780/1202 ms. Reported Success 100% for each role is not proof every action was useful or applied.

Commands: PRESS_BALL 198, RESET 64, MOVE_TO 27, CLEAR_OVERRIDE 21, INTERCEPT 14, MARK 3. No explicit PASS, SHOOT or GK_DISTRIBUTE despite two goals. The engine's default behaviour remains material. AI Overview's causal claims are unverified.

The 64 team-wide RESET commands are a concrete coordination concern: they can undo other players' overrides. Next isolated candidate **A0-M2-no-reset** appends a RESET prohibition to all five A0 prompts, retains Nova/unset inference/tools/formation, and uses player-local CLEAR_OVERRIDE when releasing control. This candidate must pass a genuinely fresh Fitness invocation before live comparison.

## Same-input model probes

In MID Harness Playground with tools disabled and A0 FWD1 system prompt, the observed kickoff wrapper was tested once per model in a new session. Nova 2 Lite: 670 ms; Claude Haiku 4.5: 1382 ms; Claude Sonnet 4.6: 1226 ms. All returned valid player-3 MOVE_TO JSON. Targets and tokenization differed. See `model-probes.json` for exact outputs and limits. These single probes do not rank model strength or establish a latency distribution; Nova remains the live control for now.

The no-RESET candidate was installed on all five roles and all five observed scrimmage sessions were stopped before a fresh test. It returned **1/5** (MID PASS). GK showed AGENT_RUNTIME_ERROR HTTP502; DEF showed NO_PARSE; detailed FWD failure codes were not captured. No live match was initiated on this failing candidate. Next **A0-M3-no-reset-no-tools** removes tool access for the remaining four roles while retaining those prompts/model/unset inference/formation. This is a separate candidate, not a clean no-RESET-only live comparison.

**A0-M3-no-reset-no-tools passed 5/5 Fitness** after all five observed scrimmage sessions were stopped and the portal reloaded. All five roles now use no-reset/ prompts, Nova 2 Lite, inference unset, tools=[], no Memory/Gateway, formation2-0-2. Reported5commands100%active; displayed0ms is not an LLM speed claim. The next initiated live match uses this configuration. Its test gate passes; match quality is pending.

## Live-04: no RESET, but no improvement established

A0-M3 lost 0:1 at home to Matrix_7. Shots4:6, on target0:1, possession43%:57%. Its115commands averaged3042ms: PRESS_BALL64, MOVE_TO25, INTERCEPT14, MARK11, FOLLOW_PLAYER1; **RESET0**. Role latencies GK/DEF/MID/FWD1/FWD2:94/2908/2837/3330/5066ms. Reported Success100% for each role. Opponent reported0commands, yet won with built-in engine play. The RESET prohibition took effect, but latency and attacking quality did not improve in this one uncontrolled match. A second live match was initiated with unchanged M3 before drawing a policy conclusion.

Tournament UI states win=3points, draw=1, loss=0; ties use goal difference, goals scored, then wins. The team summary showed15matches,8wins,7losses, but its leaderboard row still showed13matches/7wins. Treat ranking as stale until those views agree. Runtime OTEL tables currently show sampled Fitness/Playground sessions; actual live-match payloads have not been recovered, so do not invent their possession contract.

Next investigation after the unchanged control: coordinated off-ball shape and possession recognition. No explicit PASS/SHOOT in the last two reports suggests checking the current state contract before merely increasing aggression. The older H3 candidates were not fairly evaluated through fresh Fitness sessions; they remain candidates, not proven failures or winners.

## Live-05 unchanged M3: 2:0 No Context FC

The second M3 match ended in a 2:0 home win. Shots4:5, on target2:0, possession40%:60%. Our324commands averaged1347ms; PRESS_BALL312 and CLEAR_OVERRIDE12, no RESET. Role latencies GK/DEF/MID/FWD1/FWD2:1103/1290/1362/965/1279ms, reported Success100% each. Opponent21commands at2ms average. M3 currently has one win and one loss in two uncontrolled live games; no claim of stronger policy.

The96% PRESS_BALL mix does not resemble the intended differentiated role policy, especially GK. Actual live inputs and fallback application have not been recovered. Check latency/context and policy adherence; do not infer a specific fallback mechanism. Native configuration at baseline used a150-message sliding context window. A possible isolated next experiment is reducing this window (e.g.10messages) while retaining model/prompts/tools: repeated full game states may grow context, but that is a hypothesis requiring a measured live comparison. Do not add Memory to an already slow path without measuring it. Coordinated one-presser/off-ball support remains another separate prompt candidate.
