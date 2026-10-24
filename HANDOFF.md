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

Current focus at09:18UTC: test a transport-only R1 revision before adding tactical
complexity. V5 generated genuine live choices but two latest games lost0:1/0:2.
R1 model latency alone was411–497ms; this does not measure action application.
DEF logs showed Fitness requests and no matching requests for those two games.
V6 returns one completed JSON array instead of an SSE JSON string, keeping
v5 policy; AWS READY observed, five native gates in progress. Only FWD1 uses
R1; the other four remain original M7 Harness. The private checkpoint and
fresh runtime receipt supersede this snapshot.

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
