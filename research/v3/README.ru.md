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

**M4 passed the post-reset UI Fitness gate5/5**: five commands,100%active, displayed0ms (not a speed claim). Saved configuration is verified on all roles, including cleaned GK prompt and context10. The portal also displayed8MATCH WIN STREAK, which spans previous/transition stages and is not an M4 performance estimate. Next manually initiated matches will observe the fully verified M4 setup.

## M4 live13–14: RESET returned; no latency conclusion

First manually initiated post-verification M4 match beat DarkHorse_AI2:0 at home:370commands,869ms, shots5:4, on target2:0, possession35%. Counts PRESS_BALL182,MOVE_TO107,RESET57,CLEAR_OVERRIDE16,INTERCEPT6,FOLLOW_PLAYER1,MARK1. The57RESET commands violate the saved prompt instruction. Possible live overrides/session reuse or instruction non-adherence remain hypotheses; no cause is verified. The source prompt still positively lists RESET in its available-command schema, then prohibits it in an appended coordination rule. This conflict is a concrete prompt defect worth removing in a later separate candidate, but do not assert it caused the report.

An unchanged-setup away match appeared in history against EPAM Spor:0:1 loss, shots6:4, on target0:1, possession49%. Only7CLEAR_OVERRIDE commands at3ms, opponent7CLEAR at1ms. Manual initiation was not verified. This is not an LLM latency result or proof the live game used the saved policy. M4 has one verified manual win plus this background/uncertain-initiation loss; context10 is not established as a fix or stronger setup. Keep the controls separate and collect another manually initiated match before changing configuration.

## Next candidate: schema cleanup and possession readiness

`A0-M5-schema-clean` is prepared, not installed: remove RESET from the positive command description/enum while retaining the explicit ban. All other prompt text and planned M4 settings are identical.

Before deployment, seven Playground probes used the M5 FWD2 prompt as an unsaved override with separate stopped/new sessions. Synthetic states derive from the observed kickoff structure, adding explicit possession fields. Nova2Lite chose SHOOT for HOME(645ms) and MOVE_TO for teammate possession(902ms), but chose MOVE_TO instead of SHOOT in both AWAY samples(600/627ms). Haiku4.5 chose the expected category in all three cases: AWAY SHOOT1347ms, HOME SHOOT1393ms, teammate MOVE_TO1329ms. Exact outputs and limits are in `possession-probes.json`; cases are in fixtures/. This is evidence for a future limited Haiku forward trial, not proof of superior match strength. No live Harness model was changed during these probes.

## Live15 M4: 3:0 No Context FC

Second verified manually initiated M4 match won3:0: shots6:3,on target3:0,possession20%,400commands1124ms. MOVE_TO249,PRESS_BALL109,CLEAR_OVERRIDE20,SHOOT16,INTERCEPT4,GK_DISTRIBUTE1,MARK1;RESET0. Role latencies1044/1408/1289/992/1306ms,reportedSuccess100%. Both manual M4 games won, but RESET appeared in one and not the other. Context size remains an unproven cause. An uncertain-initiation background M4-era loss is recorded separately.

M5 schema-clean prompts were installed as GK13/DEF19/MID15/FWD1 14/FWD2 13. All five immutable saved views matched the complete normalized source prompt, Nova2Lite, inferenceunset and context10. This removes the positive RESET enum/definition without changing role tactics or model. Post-reset Fitness and live results are pending.

**M5 passed post-reset UI Fitness5/5**, five commands100%active and displayed0ms. Treat this as the UI gate, not a speed measurement or proof every role generated anew. An incoming BOYS753 match appeared during the update; no new manual match was launched over it. Its exact versions at kickoff are unverified, so keep it outside the clean M5 cohort.

## Incoming BOYS753 win and first M5 manual game

Transition match BOYS753 ended away1:0:shots12:1,on target1:0,possession32%,9commands3ms(PASS5,CLEAR_OVERRIDE4). This is not evidence of model speed/policy inference, and exact kickoff versions were not verified. It remains outside the clean M5 cohort. First manual post-verification M5 match was then requested without a visible incoming LIVE banner.

Latest captured leaderboard row:rank16,51points,24played17wins7losses,goals38:18(+20). It moved fromrank14/48points during the same observation interval, so ranking is dynamic. Summary still20played14wins6losses70%; history UI also limits to20records. Recent/rolling scope may explain part of the discrepancy, but was not verified. Preserve both sources and do not infer table totals from summary.

AWS documents per-invocation model/systemPrompt overrides in [Harness models and instructions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-models.html) and [InvokeHarness](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore/client/invoke_harness.html). A caller can replace saved defaults for one call. This confirms the API capability only; no actual football live override payload was recovered. Therefore saved-version checks and native probes must remain separate from proof of what every live invocation used. Do not diagnose a game-side override merely from RESET or latency reports.

## Live17 first clean M5: Neman Grodno1:2 after extra time

First verified manually initiated M5 match lost1:2: shots4:11,on target1:2,possession57%,10CLEAR_OVERRIDE commands2ms. Role latencies2/2/2/1/1ms,reportedSuccess100%. This is not evidence of model-speed or policy execution and does not establish a schema-cleanup effect. Keep M5 for another unchanged manual game before a separate model trial; do not rewrite tactics from AI Overview causal claims.

## Live18 unchanged M5:1:0 Amber Arcs2

Second M5 manual control won1:0:shots12:4,on target1:0,possession39%,4CLEAR_OVERRIDE commands2ms,all role latencies2ms,reportedSuccess100%. The two clean manual M5 games are1win/1loss, both with only low-millisecond CLEAR commands. This does not establish model execution or a tactical effect of schema cleanup. Next candidate will isolate a FWD2 model change motivated by the earlier HOME/AWAY possession readiness probes, while retaining prompts/context/tools/formation.

## M6: isolated Haiku4.5 FWD2 trial, verified gate

A0-M6-haiku-fwd2 changes only FWD2 model relative to M5, to global.anthropic.claude-haiku-4-5-20251001-v1:0. GK/DEF/MID/FWD1 remain Nova2Lite. All five use the same schema-clean/ prompts, tools=[], inferenceunset, sliding context10, no Memory/Gateway, formation2-0-2. FWD2 immutable version14 was Ready and its complete normalized prompt matched the same source; model ID, unset inference and window10 were verified. Other role versions remain13/19/15/14.

A native saved-configuration FWD2 canary, without model/prompt override, returned SHOOT player4 BL power0.8 for the synthetic AWAY-clear-shot input,2239input/43outputtokens,3058ms reported Playground latency. Its test session was stopped. This confirms availability and one basic category decision, not live match strength. All five observed scrimmage sessions were then stopped and the portal reloaded. **M6 passed UI Fitness5/5**,5commands100%active0ms. Initial portal rendering still labelled FWD2 Nova; on completion it showed Allowed · Haiku4.5, without ARN edits. Do not infer a persistent metadata mismatch from an intermediate page render. First manually initiated M6 live match was requested after the final model label and gate were verified.

Read-only CloudShell diagnostics found recent DEF main-runtime startup events around21:50UTC, while the separate Application Logs stream last showed19:54UTC. Searching the main group after21:40 for the actual Neman game ID returned0matching events. This did not recover the live invocation payload and does not prove absence of inference, caching or a game-side override. Raw IDs and logs remain private. No access policy changed.

## Live19 first M6:0:1 BlackEagle; movement-heavy attack

M6 lost its first manual match0:1. Shots6:4,on target0:1,possession55%.335commands81ms:MOVE_TO285,INTERCEPT24,CLEAR_OVERRIDE12,PASS8,GK_DISTRIBUTE4,PRESS_BALL1,SHOOT1. Role latencies86/102/86/79/88ms,reportedSuccess100%. This is a movement-heavy aggregate with little explicit shooting, but actual per-tick Haiku invocation and the cause of the loss remain unverified. A second unchanged M6 game was requested before drawing a model conclusion.

Two additional Playground-only prompt probes used Nova on the same synthetic AWAY-shot case while M6 remained saved: existing compact/fwd2.txt returned an invalid empty[](1361input/2output,621ms). identity/fwd2.txt adds explicit wrapper decoding/team/player identification to the M5 source and returned a valid MOVE_TO(0,20,false),2030input/40output,687ms. Both sessions were stopped; neither variant was installed. See prompt-readiness-probes.json for exact data.

Evaluation clarification: earlier Nova AWAY MOVE_TO outputs are valid commands. They miss our expected SHOOT category, which is a tactical readiness heuristic, and do not independently prove incorrect identity/possession parsing. Haiku's category result motivated a bounded trial, not a model-strength ranking. The compact empty[] is a confirmed format failure. Keep these evidence classes separate.

## Live20 unchanged M6:3:1 AWSenal

Second M6 manual game won3:1:shots7:4,on target3:1,possession31%,16CLEAR_OVERRIDE commands1ms;all role latencies1ms,reportedSuccess100%. Earlier M3 also beat AWSenal with a low-millisecond CLEAR-only report. This is not proof of Haiku inference or a model-strength gain. The first two M6 games are1win/1loss; preserve the working configuration for further games rather than force an unsupported model conclusion. A third manual M6 was requested after the match finished.

Formation selector was opened and closed with Done at the same2-0-2 value. It displayed two forwards and two defenders as starting shape; no formation was changed. Other variants require cycling the selector and are not yet enumerated. A1-1-2 trial remains a future hypothesis, not an installed setup.

## Live21 unchanged M6:1:3 Amber Arcs2; scheduling limit verified

Third M6 manual game lost1:3:shots3:6,on target1:3,possession36%,16CLEAR_OVERRIDE commands2ms;role2/2/2/2/1ms,reportedSuccess100%. M6's three clean manual games are1win/2losses, with mixed report regimes. No Haiku strength effect is established.

A normal Find opponent click in a second portal tab, while the first game was visiblyLIVE, was rejected by the server because a team already had an active match or pending invitation. The rejection was cancelled; no second game was created. Keep serial scheduling and do not repeat or bypass this constraint. The enabled lobby button alone does not prove concurrency is allowed.

Next candidate A0-M7-formation121 changes only starting formation relative to M6, from2-0-2 to1-2-1. Hypothesis: more central starting presence and an earlier passing link. The models, prompts and Harness versions remain identical to M6. Formation selector was cycled to1-2-1 and Done; profile showed1-2-1 afterward. Reload verification and UI Fitness are pending. Intermediate animated selector labels are not a complete formation catalog.

**M7 formation1-2-1 persisted after profile reload and passed UI Fitness5/5**:5commands100%active0ms,portal fourNova/oneHaiku labels verified. No Harness configuration changed, so this formation-only check did not repeat the earlier scrimmage-session reset. It is a UI gate, not proof of new model generation. First manual M7 live match was requested after these checks.

## Live22 first M7:2:0 Agentic United1

Find opponent now exposed a READY/NOTREADY/INMATCH list with Surprise me. Agentic United1 was enabled and selected; the actual LIVE header confirmed the same opponent. A clicked Find can be an intermediate selector, not a started game.

First M7 match won2:0:shots4:3,on target2:0,possession55%,370commands425ms. MOVE_TO162,MARK69,PRESS_BALL68,INTERCEPT29,PASS19,CLEAR_OVERRIDE13,SHOOT8,GK_DISTRIBUTE2;RESET0. Role latencies459/448/435/447/438ms,reportedSuccess100%. This is a role-diverse issued-command report and a useful repeat-opponent reference. M3 previously beat the same name1:0and2:0, but its other settings and date differ; no isolated formation-strength conclusion is established. FWD2's438ms report does not prove per-tick Haiku inference. Keep M7 unchanged for repeat controls.

After live22, another normal Find was rejected. On returning to the lobby, an active Goalpost Shifters banner was present; WATCH opened an AWAY live game. The request actor is unverified, so do not call this a successfully selected repeat opponent. Saved M7 configuration stayed unchanged. Inspect the same viewer rather than retrying Find.

Fresh leaderboard snapshot:rank13,63points,31played21wins10losses,goals47:25(+22). Summary19played14wins5losses74%, while history caps20 and includes aLIVE entry. That is consistent with recent/capped-view scope, but the exact implementation remains unverified; keep the sources separate.

## Live23 M7 observed away:1:3 Goalpost Shifters

The active-banner game ended1:3. Shots3:7,on target1:3,possession62%,362commands79ms:MOVE204,PRESS79,INTERCEPT25,PASS17,SHOOT16,CLEAR12,MARK9. Role latencies87/79/78/84/77ms,reportedSuccess100%. Sixteen issuedSHOOT commands correspond to only3teamshots; command issuance and useful application remain separate evidence. Request actor is unverified; saved M7 remained unchanged. Both M7 observed outcomes(2:0 win and1:3 loss) are retained, with selection/initiation details, without a formation-strength claim.

## Live24 M7:1:0 Lighting Cloud

Third observed M7 outcome won1:0:shots10:0,on target1:0,possession39%,117commands3365ms(INTERCEPT83,PRESS25,MOVE5,CLEAR4). Role latencies611/3806/4205/4086/4057ms,reportedSuccess100%. No issuedPASS/SHOOT despite10teamshots. Issued-command mix, latency and applied engine actions remain distinct. Two native FWD1 probes ran during part of the match; a possible load effect was not isolated. M7 observed series is2wins/1loss, with different opponents and initiation details retained.


## Live25 unchanged M7:0:2 AWSenal

Fourth observed M7 outcome lost0:2:shots4:8,on target0:2,possession61%,6CLEAR_OVERRIDE commands1ms; role1/1/1/0/0ms,reportedSuccess100%. This does not establish per-tick inference or formation/model strength. M7 observed series is2wins/2losses, retaining both manual and uncertain-initiation outcomes. Earlier wins against the same opponent do not guarantee repeat results.


## Routing laboratory: mixed synthetic results, no live deployment

Twenty-two Playground probes are recorded in routing-probes.json, including failed controls. Saved M7 remained unchanged. FWD1 Nova changed direction between modeTeamId variants in wrapped synthetic inputs; appended team-routing rules gave mixed forward targets and a wrong-side GK recovery. Original GK Nova and Haiku also chose negativeX in the AWAY wrapped recovery case. These are not proof of a live root cause.

A narrower GK candidate moved identity/recovery rules to the top and added both HOME/AWAY examples. V1 passed wrapped recovery on Nova(+49AWAY,-49HOME) and Haiku(+49AWAY), but failed wrapped GK-possession by returning MOVE_TO. V2 added possession precedence; wrapped possession still returned MOVE_TO, while direct prompt-value input returned GK_DISTRIBUTE. This exposed an important input-shape sensitivity. The actual live caller payload was not recovered.

Direct-input controls retained the same synthetic state: original GK returned MOVE_TO(-40) in AWAY recovery and GK_DISTRIBUTE in AWAY possession. V2 returned +49 in AWAY recovery and GK_DISTRIBUTE in possession, but also incorrectly chose GK_DISTRIBUTE in HOME teammate-possession recovery. Therefore neither candidate is ready for deployment. team-routing/ and gk-routing/ are explicitly laboratory-only. The existing live M7 config and 5/5 gate remain the working baseline.

Official sample identity mapping: [agent_base.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/lib/agent_base.py) obtains controlled teamId from the outer input; [state.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/lib/state.py) maps team0 HOME to own goal negativeX and team1 AWAY to own goal positiveX. This reference does not establish the exact managed live invocation payload used in these matches.


## Live26 M7 plus Shout:1:0 Hail Mary in overtime

The spectator Unity START control was opened and exposed a coach text field/Shout button. Two own tactical instructions were sent: at about00:33/0:0, goalkeeper stay near own goal, defender cover, midfielder forward pass, forwards width and clear-shot priority; during0:0overtime, explicit forwards SHOOT when possessing the ball in range with a clear lane and midfielder safe support pass. Both messages appeared in Coach Live Feed after an initial delay, confirming UI delivery, not agent adherence. Exact own text is retained on the match record. The workshop guide says coaching arrives via teamChat if the implementation consumes it, and previous-match instructions are not automatically retained. Do not claim persistent learning/fine-tuning.

Result1:0 in overtime:shots10:0,on target1:0,possession56%,379commands845ms. PRESS184,MOVE152,INTERCEPT31,CLEAR12;noSHOOT/PASS. Role latencies644/907/942/629/902ms,reportedSuccess100%. Teamshots and issued commands remain distinct; no verified causal benefit from coaching. M7's five observed results are3wins/2losses, but this game has an explicit coaching intervention and one earlier loss has unverified request actor.

Fresh table around this completion:rank12,69points,35P23W12L,goals50:30(+20). Summary20P14W6L70% remains a different/capped scope; exact implementation not verified. Preserve source scopes and dynamic timing.


## Live27 unchanged M7:2:1 Meerut United in overtime

No Shout/native probe or Harness change during this game. It won2:1:shots12:3,on target2:1,possession45%,659commands1093ms. MOVE314,PRESS246,CLEAR36,PASS27,SHOOT19,GKDIST17. Role latencies932/1233/1264/1230/983ms,reportedSuccess100%. The viewer stopped updating overtime commentary while lobby also showedLIVE. Reloading the SAME viewer recovered the terminal2:1; no replacement match was started. Do not classify a stalled observation as a failed server process.

M7 has six observed outcomes4wins/2losses, including one coached win and an earlier loss with unverified request actor. Different opponents, command-report regimes and interventions prevent a causal formation-strength estimate.

## M8 formation1-1-2 trial

The GUI selector exposed1-1-2 with FWD FWD /MID /DEF /GK. This aligns the starting rows with the existing assigned role prompts better than1-2-1, whose starting middle row included FWD4. This is a testable tactical hypothesis, not proof that initial rows determine later behaviour. Selected1-1-2 and Done; profile displayed1-1-2. Reload verification and UI Fitness are pending. All five Harness models/prompts/versions/settings remain inherited M7. The aggressive workshop library was reviewed; its all-out setup intentionally exposes an empty goal. It was not installed.


**M8 formation1-1-2 persisted after reload and passed UI Fitness5/5**:fivePASS,5commands100%active0ms,portal fourNova/oneAllowedHaiku confirmed. No Harness configuration was edited and no scrimmage reset was repeated for this formation-only change. This verifies the UI gate, not fresh generation/model speed. First post-gate live match is next.


## Live28 first M8:1:0 Shalqar United in overtime; RESET recurred

First post-gate M8 game won1:0 without coaching/native probes. Shots4:6,on target1:0,possession42%,325commands815ms. PRESS216,INTERCEPT70,CLEAR20,MOVE11,SHOOT5,RESET2,GKDIST1. Role latencies604/826/937/815/888ms,reportedSuccess100%. Two issuedRESET commands violate the saved schema-clean prompts: positive RESET definition/enum was removed at M5 and explicit prohibition retained. This does not identify the actual live payload or emitting role and does not by itself establish an override, cache or model cause. Do not claim the cleanup guaranteed compliance. Keep M8 unchanged for a second observation rather than attribute a first win to formation strength.


## Live29 unchanged M8:0:0 Sporting Lambda; primary stats unavailable

Second M8 game drew0:0 after overtime. SixCLEAR_OVERRIDE commands1ms;opponent7commands2ms(CLEAR6,PASS1);own role2/2/1/1/1ms,reportedSuccess100%. The rendered report has NO primarySTATS table, so shots/on-target/possession are null, not zero. The viewer header remainedLIVE after full-time commentary; reload of the same viewer confirmed Draw0:0. No coaching or native test ran during the game. M8 currently has one win and one draw; different command-report regimes still prevent a formation-strength conclusion.

report_parser.py now requires explicit --allow-missing-stats to preserve unknown values when an inspected report genuinely omitsSTATS. Default behaviour remains strict; a present malformed table still fails. Four focused tests passed, plus seven actual prior HOME/AWAY reports matched their stored metrics. AI Overview is not used to fill missing numbers.

## Command-guard laboratory: no observed readiness advantage

After the game ended, original FWD1 Nova and a command-guard/ candidate were compared on two direct synthetic input cases: a teamChat request to RESET all players, and a request to control all0..4. The candidate moves the existing ban to the beginning and explicitly preserves it against unlockedCommands/teamChat. All four calls returned one valid MOVE_TO for player3 with noRESET; each session was stopped and original prompt restored. Both variants passed2/2; no comparative gain is established and the candidate was NOT installed. Other four role candidate prompts remain untested. Exact outputs/tokens/latencies/hashes and input-shape limits are in command-guard-probes.json.

A focused read-only AWS Harness table recheck showed latest versions stillGK13/DEF19/MID15/FWD1 14/FWD2 14. No configuration drift was observed; this does not identify which live payload/role produced the two earlierRESET commands.


## Live30 unchanged M8:1:0 Matrix_7 in overtime; rank9 snapshot

Third M8 game won1:0 with no coaching/native probes. Shots20:0,on target1:0,possession40%,543commands212ms. MOVE332,MARK145,PRESS25,INTERCEPT23,CLEAR14,GKDIST4;RESET0,SHOOT0,PASS0. Role latencies80/347/485/77/119ms,reportedSuccess100%. Twenty teamshots and only one on target do not translate directly into issued SHOOT commands; actual model payload/application remains unknown. M3 earlier lost0:1 against this opponent name, but settings and time differed, so no isolated M8 effect is established. M8 first three results are2wins/1draw. Retain the unchanged candidate for more games.

Fresh leaderboard:rank9,79points,39P26W1D12L,goals54:31(+23). Summary20P13W1D6L65% differs from the cumulative table; preserve both source scopes. This is a top10 observation at capture time, not a contest victory or guaranteed final rank.


## Live31 unchanged M8:2:1 Agentic Arsenal; RESET5

Fourth M8 game won2:1 after trailing0:1. A possible Shout intervention was considered, but no field was visible in the current viewer and no instruction was sent. No native probe or Harness change during the game. Shots13:3,on target2:1,possession44%,332commands858ms. MOVE151,PRESS80,FOLLOW33,SHOOT25,CLEAR12,PASS10,INTERCEPT9,GKDIST6,RESET5,MARK1. Role latencies655/926/1032/677/916ms,reportedSuccess100%. The RESET recurrence remains unexplained; the saved source ban is not a hard execution guarantee. Overtime was not independently captured. M8 first four outcomes are3wins/1draw.


## Direct FWD1 model comparison: retain Nova; no M9 deployed

After live31 finished, the same schema-clean/fwd1.txt was tested with Nova and a Playground-only Haiku override on three direct JSON inputs. Nova:HOME SHOOT724ms,AWAY validCLEAR655ms,teammate MOVE611ms. Haiku:HOME SHOOT1364ms,AWAY SHOOT3119ms,teammate MOVE1397ms. Expected action categories are tactical heuristics, not proof of parsing or match quality; both models produced player3 command arrays in all cases.

The initial array-only reading missed a material format violation: the Haiku AWAY reply appended a Reasoning section and seven extra visible text blocks. Therefore Haiku matched3/3 expected categories but only2/3 strict JSON-only contracts; Nova matched2/3 categories and3/3 contracts. The hypothetical FWD1 Haiku upgrade was rejected and no M9 installed. All six test sessions were stopped; saved M8 remained unchanged. The complete-text evaluator also rechecked22routing+4command-guard snapshots: each had one full JSON text block matching its stored array. This was a focused audit, not all historical probes. See fwd1-direct-model-probes.json for hashes/tokens/outputs and input/format limits; extra reasoning is not published.

A possible runtime output filter was investigated in [AWS lifecycle-hook documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-lifecycle-hooks.html). Documented hooks operate at invocation/tool boundaries; after_invocation runs after completion and cannot retract streamed output. These hooks therefore do not provide the proposed post-response RESET-text rewrite in the current tool-free setup. This is an applicability conclusion, not a tested hook deployment. No Lambda, permissions, tools or hooks were added.


## Live32 unchanged M8:2:0 Apocalypse

Fifth M8 game won2:0 without coaching/native probes. Shots8:0,on target2:0,possession53%,375commands499ms:MOVE367,CLEAR8,allothercategories0. Role latencies519/514/503/500/517ms,reportedSuccess100%. The report contains onlyMOVE/CLEAR despite two goals and8teamshots; actual applied scoring actions and per-call payload remain unverified. M8 firstfiveoutcomes4wins/1draw. Retain the unchanged working setup for the remaining live series; no new model/prompt changes planned before the deadline without a concrete issue.


## Live33 unchanged M8:2:0 Hail Mary; rank9/88points

Sixth M8 game won2:0 with no coaching/native probes. Shots7:2,on target2:0,possession33%,329commands824ms. MOVE166,PRESS128,CLEAR16,INTERCEPT14,MARK3,SHOOT2;RESET0. Role latencies645/968/931/629/909ms,reportedSuccess100%. Earlier M7 beat this opponent1:0 with coaching under different conditions; this repeat does not isolate formation or coaching effects. M8 firstsixoutcomes5wins/1draw.

Fresh cumulative table:rank9,88points,42P29W1D12L,goals60:32(+28). The rendered summary snapshot is stored separately in standings.json; our33 observed reports do not cover every account match. Rank is dynamic.


## Live34 unchanged M8:1:0 Amber Oars2; rank8/91points

Seventh M8 game won1:0 without coaching/native probes. Shots7:1,on target1:0,possession36%,264commands787ms. PRESS146,MOVE92,CLEAR15,INTERCEPT9,MARK1,SHOOT1;RESET0. Role latencies594/810/909/611/928ms,reportedSuccess100%. M8 firstsevenoutcomes6wins/1draw, still an uncontrolled series.

Fresh table:rank8,91points,43P30W1D12L,goals61:32(+29). It is tied on points with the seventh team but behind on goal difference; do not call it seventh. Summary remains separately stored.


## Live35 unchanged M8:1:0 Singularity FC; rank7/94points

Eighth M8 game won1:0 without coaching/native probes. Shots9:4,on target1:0,possession44%,330commands74ms. MOVE142,CLEAR125,PRESS40,MARK20,PASS3;RESET0. Role latencies80/83/80/75/81ms,reportedSuccess100%. Opponent issued only4CLEAR commands2ms despite its previously captured8W2D1L record. Prior win record does not establish that opponent models actively ran in this game. M8 firsteightoutcomes7wins/1draw.

Fresh cumulative table:rank7,94points,44P31W1D12L,goals62:32(+30). This is the current observed position, not a contest victory. Summary stored separately.
