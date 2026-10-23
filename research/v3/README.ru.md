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

Captured A0 prompts are archived in `a0/`; the GK capture was later found to include a UI label, as noted below. A0 uses Nova 2 Lite, unset inference configuration and Allowed tools `*`, with no Memory/Gateway. The five original prompts include the tactics already present at session start; “A0” does not mean an untouched workshop template.

AWS Console does not save a panel with all inference fields cleared: its Save button becomes disabled. Simply clearing the fields and saving the Harness retained the old parameters. Switching the unsaved model-source selection away from Bedrock and back reset the inference configuration. Saved version inspection then confirmed `Inference configs -`, Nova 2 Lite, and All tools (*). No alternative model source or credentials were saved.

Public-safe setup manifests and prompt hashes: `setups.json`. Live report metrics: `matches.json`. Raw AWS identifiers, account information, credentials, screenshots and traces remain private under ignored `.local/`.

Full A0 restoration was verified in immutable saved version views for all five roles: Nova 2 Lite, no inference config, All tools (*). Fitness still returned 2/5 (GK/FWD2 PASS; DEF/MID/FWD1 FAIL). DEF reported 0/1 active ticks and missing team PASS. This reused-session result did not establish how a new A0 model invocation would behave, and did not identify the underlying cause. Next isolated diagnostic: one fixed PASS response on DEF.

## Native Harness response and session diagnostic

A fixed PASS array on DEF produced the exact valid JSON in a new Playground session (reported model latency 595 ms), while Fitness still returned 2/5. A fixed `{"commands":[...]}` envelope also left Fitness at 2/5. Neither diagnostic is a playing strategy; DEF was restored to A0 afterwards.

The Harness dashboard route returned a permissions error, but the actual managed Runtime's **View dashboard** route works. Its OTEL sessions expose a persistent scrimmage session reused by repeated Fitness runs. Recent traces contain only two `AgentCore.Harness.Invoke` spans, HTTP 200, zero model tokens, no model-generation spans. An older call in that session includes model input/output. The initial captured request contains a nested JSON-string `prompt` holding gameState/teamId/myPlayers. These observations motivate a repeated-session/replay hypothesis; the exact cache mechanism is not yet proven.

The observed DEF scrimmage session was stopped with the Console's ordinary “Stop current session and create new session” action; success was confirmed. Fitness still failed. Next control: reload the Player Portal and rerun Fitness from its fresh page state. No endpoint permissions or IAM policies were changed.

After restoring DEF A0, stopping its observed scrimmage session and reloading the portal, Fitness improved to **3/5**, with DEF now PASS. This is the first verified change in the Fitness outcome. The exact contribution of session termination versus fresh portal state is not isolated yet. MID and FWD1 scrimmage session identifiers were separately observed in Runtime OTEL tables and stopped through the same ordinary Console operation; their results are pending.

Stopping the separately observed MID/FWD1 scrimmage sessions, reloading the portal and rerunning Fitness yielded **4/5**: FWD1 now PASS, MID now **NO_PARSE** instead of the previous stale 0/1-active-command result. Its new tip says it responded once but the response was not valid JSON with a commandType field. This is materially different evidence. Next isolated change: retain MID's A0 prompt/model/unset inference, remove its allowed-tools wildcard, stop that Fitness session and rerun from a reloaded portal. Earlier prompt/model/tool trials that reused the old scrimmage session cannot establish that those candidates fail on a fresh invocation.

## Verified Fitness recovery: A0-M1 — 5/5

After retaining MID's A0 prompt/model/unset inference, removing only MID's tool wildcard, stopping its observed scrimmage session and reloading the portal, Fitness displayed **All agents passed. Ready to play.** All five positions PASS; Practice and Find opponent enabled. It reported 5 commands and 100% active. Its displayed 0 ms is not evidence of real model latency.

The reproducible working setup is **A0-M1** in `setups.json`: all five A0 prompts, Nova 2 Lite, inference config unset; Allowed tools `*` for GK/DEF/FWD1/FWD2, empty list for MID; no Memory/Gateway; formation 2-0-2. This is a verified connectivity/format/activity gate, not a proven winning policy.

Recovery was observed after resetting the repeated scrimmage sessions and reloading the portal, then addressing the newly observed MID NO_PARSE result. The reset/reload procedure was followed by changed DEF/FWD1 results, and restricting MID tools was followed by its PASS. The exact internal cache mechanism and the individual contribution of reset versus reload are not proven. Earlier same-session candidate failures must not be treated as fresh model comparisons.

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

## Live-06 unchanged M3: 1:0 Agentic United 1, 454ms

Third M3 match won1:0. Shots5:4, on target1:0, possession47%:53%. Our335commands averaged454ms; per-role GK/DEF/MID/FWD1/FWD2:453/446/458/444/456ms, reported Success100%. Commands: MOVE_TO130, MARK88, PRESS_BALL46, INTERCEPT41, CLEAR_OVERRIDE11, PASS9, SHOOT7, GK_DISTRIBUTE3; RESET0. Opponent8CLEAR commands at3ms average.

This changes the next action. M3 now has2wins/1loss in3uncontrolled games, and unchanged configurations showed3042 ->1347 ->454ms. The third game recovered a role-diverse command mix, including passing, shooting and GK distribution. The cause of the latency changes is not identified; warmup/service variability is a hypothesis. Long context is not established as the problem. The150-message sliding window was confirmed in the live MID edit form and left unchanged; that form was cancelled. Defer the proposed context reduction and collect further unchanged controls before tuning. Do not rewrite possession logic based solely on the earlier missing action types.

Leaderboard follow-up snapshot: team summary17matches/10wins/7losses/59%; table row rank19,15played/9wins/6losses, goals24:16, difference+8,27points. Both views advanced but retained a two-match difference. The cause may be scope or lag; the earlier assumption that the row is necessarily stale is unproven. Do not replace the table's27points with10*3 or derive an unobserved current rank from summary counts.

## Live-07 unchanged M3: 2:0 AWSenal; inference not established

Fourth M3 match won2:0. Shots8:1, on target2:0, possession34%:66%. Report shows only11CLEAR_OVERRIDE commands at1ms average; role latencies2/1/1/1/1ms, Success100%. Opponent19commands at3ms. No RESET. This report does **not** establish Nova inference or prompt execution. Engine play/cache/fallback remain possibilities; no specific cause was verified. Do not call1ms a model-speed result or count this as a strong model comparison. M3 has3wins/1loss in4uncontrolled matches, with markedly different command/latency regimes. A further unchanged match is needed before any policy attribution.

After live07's1ms report, an independent native FWD1 canary used its saved M3 configuration without model/prompt override. It returned valid player3 MOVE_TO JSON (x10,y-10,sprinttrue),1747input/40output tokens,1168ms reported Playground latency. This confirms the saved Harness is available on that reference input. It does not prove the live07 game invoked it or identify why the report showed only1ms CLEAR commands.

## Live-08 unchanged M3: 1:0 Meerut United

Fifth M3 match won1:0. Shots10:2, on target1:0, possession19%:81%. Our327commands averaged1091ms; MOVE_TO142,PRESS_BALL120,CLEAR_OVERRIDE20,SHOOT18,PASS15,GK_DISTRIBUTE12; RESET0. Role latencies943/1267/1335/1255/958ms, reported Success100%. Opponent7commands at3ms. M3 now has4wins/1loss in5uncontrolled live matches. This is a useful observed series, not a controlled improvement estimate. Both1ms-clear and substantive role-diverse reports occurred with unchanged installed configuration; preserve that uncertainty.

## Consistent report recording

`report_parser.py` extracts only score, primary STATS, command counts and role performance from a locally saved rendered AX report. It ignores AI Overview explanations and omits account IDs, ARNs, URLs and raw traces. It fails on missing/unknown tables or command totals that do not add up. It does not establish model inference or action application.

Verified against independently recorded fields from seven earlier real reports (live01–07, including both HOME and AWAY), then checked against the live08 UI. Example:

```sh
python3 research/v3/report_parser.py PRIVATE_REPORT.txt --opponent 'Meerut United' --side home --id live-08 --setup A0-M3-no-reset-no-tools
```

Raw reports stay private under ignored `.local/`; review the extracted numbers before appending to matches.json.

Terminology clarification: a “fresh Fitness” in these operational notes means the documented post-session-stop/reload procedure, not proof that every role generated a new LLM response. The UI5/5 gate is verified; its displayed0ms and missing per-call traces do not establish fresh generation on all five roles. The independent saved-configuration FWD1 canary has actual input/output token counts and a generated response.

## Live-09 unchanged M3: repeated-opponent 2:0, 433ms

M3 beat Agentic United1 again,2:0 (earlier same-name opponent1:0). Shots12:3, on target2:0, possession41%:59%. Its370commands averaged433ms: MOVE_TO124,MARK103,INTERCEPT71,PRESS_BALL29,CLEAR_OVERRIDE16,PASS10,SHOOT9,GK_DISTRIBUTE8; RESET0. Role latencies440/431/447/453/439ms, reported Success100%. Opponent8CLEAR commands at2ms. M3 now5wins/1loss in6uncontrolled games, without configuration changes. Different runtime/report regimes remain unexplained; keep the working setup and collect the series rather than force an unsupported context change.

The latest verified leaderboard row is rank17,36points,18played/12wins/6losses, goals29:16(+13). Team summary is20played/13wins/7losses/65%. Both sources are retained in `standings.json`; their two-match discrepancy is not explained.

## Live-10: win with zero reported commands, context experiment justified

Unchanged M3 beat No Context FC1:0 after extra time, but the report recorded0commands and14263ms average. Shots4:5, on target1:0, possession36%:64%. Role latencies11142/18927/18937/11136/11172ms, reported Success100%. The opponent also had0commands at2ms. This win cannot validate the model policy. M3's observed series is6wins/1loss in7games, but runtime/report regimes remain highly variable.

The new zero-command/high-latency result changes the next action: test **A0-M4-context10**, retaining M3's model, prompts, tools, inference and formation while setting the sliding context window to10messages. The actual pre-change value will be recorded from each role rather than assumed. Long context is a hypothesis, not an identified cause. Preserve M3 as the control and inspect the saved configuration and post-reset Fitness before live comparison.

## GK capture correction and M4 comparison limit

Expanding the saved prompt exposed an extraction mistake: GK's captured A0 text included the interface label `Show less`. It was deployed in the historical A0/M1/M2/M3 bundles. Those files remain unchanged as records of what was actually installed; they are not claimed byte-exact copies of the original GK source. The label is removed in `context10/gk.txt`; the other four prompt texts remain identical to no-reset/. M4 therefore changes both context size and GK cleanup. Do not attribute any outcome solely to the context window. The UI label was not established as a cause of Fitness or latency failures.

All five pre-change Messages Count values were observed as150. All five context10 submissions succeeded. An incoming Octopus match and an already completed win against The Drunkards appeared during this update. Their exact configuration attribution is uncertain; record them outside a clean M4 cohort and do not launch another manual match while an incoming live banner is visible.

## Incoming/background records and M4 verification

An incoming away win over Octopus0:1 was observed while the context update was underway:335commands,84ms, possession54%, shots5:6, on target1:0. A retrospectively opened away win over The Drunkards1:2 showed565commands,77ms, possession52%, shots7:6, on target2:1. Both had role-diverse actions, but exact per-role versions at kickoff were not recovered. They are recorded as `unattributed-background`, excluded from the clean M3/M4 comparison. Local liveNN IDs indicate evidence-recording order, not guaranteed kickoff order.

All five M4 saved immutable versions were inspected: Nova2Lite, inference configs unset, sliding_window Messages Count10, and fully expanded prompt text matching context10/ after whitespace normalization. GK12/DEF18/MID14/FWD1 13/FWD2 12. The GK prompt no longer contains the UI label. This verifies configuration, not execution on every live tick. Post-reset Fitness is pending.

Official references support testing the hypothesis but do not prove a latency fix: [AWS Harness memory/truncation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-memory.html) describes retention options; [Harness operations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-operations.html) includes conversation history in model input and documents session compute; the [Strands reference implementation](https://github.com/strands-agents/harness-sdk/blob/main/strands-py/src/strands/agent/conversation_manager/sliding_window_conversation_manager.py) shows routine window management. The exact managed runtime version and any game-side overrides are not established, so effective history size and model latency still require observation.
