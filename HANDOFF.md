# Agentic FC continuation

This is the same ongoing tournament-preparation task. Read the current UI and
`.local/aws-20261024-sixhours/current-run.json` first; it is the private execution
checkpoint. Public evidence is in `research/v3/runtime-r1.json`,
`research/v3/run-20261024-sixhours.json` and `research/v3/matches.json`.

The latest direct user request starts a new eight-hour window at
2026-10-24T09:14:05Z, ending17:14:05Z (20:14:05Europe/Minsk). Stop new manual
matchmaking ten minutes before the end, preserve final artifacts and push,
then disable this task's heartbeat. **No shutdown, no Chrome/process cleanup.**
The old shutdown request was canceled. Keep VPN unchanged. Our bounded
`caffeinate -i -s -t28800` process was verified with matching system and idle
sleep assertions; display sleep is allowed. Confirm its current private PID
from the checkpoint before changing only our own timer.

Use Computer Use for AWS, the football portal and visible CloudShell commands;
local files, tests and Git are allowed. No IAM expansion, SCP bypass, local
AWS API calls, messages to people, extra Codex chats or subagents. Play serially;
inbound matches can begin independently. Check the portal before native probes
or saved AWS changes. Never stop game sessions.

Keep credentials, account/ARN bindings, raw states, private logs and foreign
chat out of public Git. The branch is `codex/football-experiments-20261023`;
draft PR5 is already attached. Preserve unrelated work.

Current focus at09:55UTC: original FWD1v16 restored in the portal for a control on1-1-2, after native/Fitness-valid R1v7 generated choices but still had poor live results. Control live57 HOMEvsGork'n'MorkBoyz is active; read checkpoint. Native-only transportv6(JSON) was rejectedNO_PARSE; v7 restores exactv5SSE. Live54 used stalev6(build-correlated), notv7. Fixed Fitness session was stopped200; thenUI5/5. Live55 manualHOME112lost0:1; backgroundlive56AWAYForza won1:0 and needs build correlation.

A buffered-SSEv8 candidate is prepared: outer async function awaits one decision, then returns a normal generator. SDK emits byte-identicalSSE, but headers now follow model work. HTTP fake-client smoke verifies completed model work before response object and exactSSEbytes. FWD1 prompt/options parity checked8fixtures;38policy/runtime/GK/observer checks pass. This is a hypothesis about eager-header consumption, not a proved cause. Runtimev7 remains untouched; check Git/latest artifact for v8 deployment status.

Separate GK code exists and is offline, not deployed. Current package now includes a dormant GK branch, but FWD1policy remains unchanged. Only0 and3 are accepted by deployer. GK has no PRESS/SHOOT/PASS/RESET, no world-frameMOVE, safe distribution and documented mirrored recovery. Eleven native GKcases are prepared. All raw bindings/private receipts remain under.local.

Execution concern: DEFrequest logs since09:20 show6Fitness events,0matchingHOME55/AWAY54/AWAY56. CloudWatch DEFInvocations since08:40 sums10 over5minutes, errorSum0 (duplicate metric dimension sets must not be added). Portal fourHarness counters remain0. This does not identify the game caller's failure, but five independent CodeRuntimes may be a practical path to verified live calls for all roles. No callerIAM changes. Before expanding, test precomputedSSEv8 and isolatedGK. Future DEF/MID/FWD2 should use coordinate-independentPASS/MARK/PRESS/INTERCEPT/SET_STANCE with single nearest eligible outfield presser, energy guards, central cover and noRESET. Do not invent worldMOVEconversion. Official Tactical guide: SET_STANCE persists until cleared; CLEAR removes own manual override, RESET clears wholeteam. Attacking stance is a candidate to improve offball depth without guessed coordinates; test one mechanism at a time.

`runtime_v1/tactics.py` is a tested **offline observer**, excluded from the
deployed package. Future integration and synthetic model-round runner are
preserved privately under `.local/aws-20261024-sixhours/adaptive-v6-design/`.
Do not accidentally deploy them with the transport comparison. The user asks
for critical self-interview rounds, formation/model comparisons, an adaptive
attack, central defensive cover, energy management and goalkeeper improvement.
Use `research/v3/adaptive-plan.ru.md` for hypotheses and rejection gates.

Do not equate Fitness5/5, reported100%Success, issued commands, possession or
synthetic rounds with live strength. AIOverview is not causal evidence. Preserve
primary numeric report tables and explicit unknowns. Shot reports currently
lack per-shot distance/outcome data; long-shot miss rates cannot be established.

Update10:10UTC: live57 control finished7:0, shots19:0, possession19%, command545(437INTERCEPT,0SHOOT), reportedavg470ms. OriginalfiveHarness plus112 remain main team. Inboundlive58AWAYvsZorja portal6239347a-0551-4901-a84f-9ac051549c6b started during native tactical model rounds, so record overlap. NoFindclicked. The first16-case benchmark now finished; all16legal and target-aligned, all own sessions stopped. Nova8cases nativewall~1.2–4.2s. Haiku highline/deepblock4cases26–33s while other4~1.6–3.6s; inspect metadata before attributing model latency. Originalrunner did not record first-content timing; newsource records headers/firsttext/firstJSONprefix and persists inflightID before calling. Needexport with model_rounds_summary.py (newlocalfile) through visibleCloudShell and save whitelisted results. Bothmodels8/8small synthetic labels are not a general match ranking.

Officialworkshop DeploytoAWSHarness tab explicitly says use HarnessARN, not underlyingRuntimeARN. It is a supported path. Missinglogs do not prove broken routing or authorizeIAMchanges. No arbitrary replacements of the working main team. The7:0control is a useful champion candidate; keep it asrollback while testingbufferedSSE.
