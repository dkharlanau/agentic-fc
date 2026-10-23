# Research sources and authority

Primary public sources inspected 2026-10-23:

1. [AFC official event site](https://agenticfootballcup.com/): 5v5, 2-second decision interval and *1-second* agent response budget.
2. [AWS official balanced team reference](https://github.com/aws-samples/sample-ai-possibilities/tree/main/agentic-football-sample-agents/ai-team-strands-balanced): player IDs/command shapes, model distribution, fallback.
3. [Shared state.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/lib/state.py): modern game-state fields, repeated agent IDs, case-normalized teamCode, unknown possession, fractional stamina.
4. [Shared fallback.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/lib/fallback.py): fallback behaviours, coordinate defaults and simplistic on-ball shot thresholds.
5. [Shared parsing.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/lib/parsing.py): commands, field bounds, team/player enforcement.
6. [AWS Gateway starter](https://github.com/aws-samples/sample-ai-possibilities/tree/main/agentic-football-sample-agents/ai-team-strands-gateway): tactical MCP tools and dual deployer warning.
7. [Gateway calculate_pass_options.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/ai-team-strands-gateway/gateway_tools/calculate_pass_options.py).
8. [Gateway evaluate_shot.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/ai-team-strands-gateway/gateway_tools/evaluate_shot.py).
9. [Gateway find_open_space.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/ai-team-strands-gateway/gateway_tools/find_open_space.py).
10. [Gateway get_defensive_assignment.py](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/ai-team-strands-gateway/gateway_tools/get_defensive_assignment.py).
11. [Older AWS game mechanics coaching notes](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-coach/kiro-football-coach/content-reference/en/game-mechanics.md).
12. User-provided Football Strategies and Agentic System workshop notes, plus three match reports.

## Contradictions to resolve against actual live tick

- **Deadline**: older coaching reference says 500ms; 2026 Cup event page says 1s. Prefer actual event deadline and server traces.
- **SET_STANCE enum**: older coaching document calls 1 DEFENSIVE and 2 ATTACKING; current balanced prompts call 1 Attack and 2 Defend. Do not use SET_STANCE until verified against game engine.
- **PASS types**: old coach guide says short/long; recent prompts use GROUND/AERIAL/THROUGH. Use the *current* prompt schema.
- **Possession**: repeated per-team 'agentId_N' prevents unique owner inference without an explicit team indicator. Source code's chosen-first policy is a known limitation.
- **Model code vs Harness**: Runtime supports programmatic fallback; Harness relies on model output format and can NO_PARSE intermittently.
- **Model latency**: averages from a game summary are not a controlled same-input benchmark and may not use identical timing boundaries.

## No invented performance guarantees

The four Gateway utility outputs are **scores from hardcoded assumptions**, not experimentally calibrated xG or pass success probabilities. No model or tactical arrangement has been proven optimal by three matches.
