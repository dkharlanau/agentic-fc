# 05 — Experiment protocol

Three supplied matches are not an A/B study. Do not change model, prompt, stamina thresholds and formation simultaneously.

## Baseline freezes

Write five exact active prompts, models, their version IDs and date into a *private* audit snapshot (redact live IDs before public sharing). Label A0. Keep A0 Harness ARN mappings intact.

## Match matrix (minimum)

| Opponent class | What it stresses | Key measure |
|---|---|---|
| Passive / baseline | Basic scoring, safe output | Goal difference, shot conversion |
| High press / attack | Turnovers, goalkeeper, coverage | Dangerous losses, shots conceded |
| Compact defence | Creation against crowded lanes | Shots on target, pass-through value |
| Strong mixed opponent | Robustness | Wins, conceded goals, error rate |

When possible pair HOME and AWAY. If the portal cannot choose sides or seeds, record actual assignment and use several games per cell. Keep Shout **off** in A/B tests.

## Ablation ladder

A0: freeze current Nova 2 Lite Harness.
B1: same model/prompt, fix only state parsing and JSON validation via Runtime.
B2: add deterministic single-press-owner arbitration and protective DEF behavior.
B3: add safe pass-vs-shot-vs-dribble ranking.
B4: add stamina-aware sprint and dynamic mode switches.
B5: compare fast-vs-large models using same saved states (then matches).
B6: optional Memory/Gateway experiments only with measured latency headroom.

**Rollback:** Any build with invalid target IDs, repeated NO_PARSE, unstable away-side commands or elevated timeout rates is reverted immediately even after an anecdotal 4–0 win.

## Quantitative acceptance (provisional)

- Unit tests: 100% pass, including HOME/AWAY, duplicate IDs and corrupted payloads.
- No structurally invalid outgoing JSON under fuzz fixtures.
- Target: >99% valid, *applied* actions across a meaningful practice sample; compare with event server figures.
- Lower bound: no meaningful decline in goals per match or sharp increase in goals conceded against **matched** opponents.
- Latency: report P50/P95/P99 and per-player timeout counts, not just mean.
- Win rate: report per opponent class with a small-sample caveat. If results are close, play more games before concluding.

## Log schema

Use JSONL with timestamp, build_hash, position, team_side, tick, phase, possession_status, confidence, stamina, distance_to_ball, selected_command, reason, fallback, latency_ms, applied, result_event. Redact personal/team credentials. *Don't* log model chain-of-thought, full sensitive prompts or participant secrets.

## Self-review after each experiment

- Did the engine actually apply our command?
- Was the ball owned by OUR player and team at the instant of decision?
- Was a miss due to aim, blocker, range, shot accuracy, stamina or timeout?
- Did the chosen presser pull DEF out of shape?
- Was the bad outcome caused by model choice or input/parser error?
- Did our change improve more than one opponent type?
