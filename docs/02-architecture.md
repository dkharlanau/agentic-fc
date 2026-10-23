# 02 — Architecture: fast path, constrained intelligence, safe output

~~~mermaid
flowchart TD
  A[Game tick: payload] --> B[Canonical state adapter]
  B --> C{Possession known?}
  C -->|confirmed| D[Situation and geometry]
  C -->|free or unknown| E[Safety / off-ball roles]
  D --> F[Rank candidate actions]
  E --> F
  F --> G{Simple & confident?}
  G -->|yes| H[Deterministic selection]
  G -->|no and budget permits| I[Optional Bedrock decision adviser]
  I --> J[Validate / rerank proposal]
  J --> H
  G -->|no time or unavailable| H
  H --> K[Per-player command schema validation]
  K -->|invalid| L[Legal fallback / built-in AI]
  K -->|valid| M[JSON encode, one command]
  L --> M
  M --> N[Game engine]
  N -. traces .-> O[Offline replay + experiments]
~~~

**The published tournament site specifies:** every two seconds all ten agents are called in parallel; each has one second to return. Do not put repeated LLM/Gateway/Memory round trips on a critical path without measured budget headroom. An older workshop coaching reference says 500 ms; verify the actual event trace, never assume latency budget from a stale document.

## Physical state

- Player IDs 0 GK, 1 DEF, 2 MID, 3 FWD1, 4 FWD2.
- Team 0 HOME attacks +x; team 1 AWAY attacks -x.
- Normalize **attacking_progress = attack_sign * x**, where HOME sign = +1, AWAY sign = -1.
- Real example fields include players[].agentId / teamCode / position / velocity / stamina / lastAction, ball.position / velocity / isFree / possessionAgentId.
- **agentId_0..4 repeats across teams.** Never identify a ball holder solely by player index.
- The code sample sometimes selects the first matching possessionAgentId; it explicitly acknowledges unresolved ambiguity.
- If a claim cannot be corroborated by a unique player or side, state is **unknown**, not FREE. Choose a conservative/off-ball response.
- Physical stamina in modern sample fixtures is a fraction 0..1; static stat skill values in the workshop are 1..100. Distinguish them explicitly.

## Action horizon

One-shot: MOVE_TO, PASS, SHOOT, GK_DISTRIBUTE (duration=0).
Maintained: PRESS_BALL, INTERCEPT, MARK, FOLLOW_PLAYER (positive tick duration; exact semantics should be confirmed by current match inputs).
Special: CLEAR_OVERRIDE deliberately returns control to built-in AI; do not equate it with standing still. RESET is team-wide and forbidden for individual-player routine logic. SET_STANCE enum differs across versions; disable until current runtime confirms values.

## Shared policies without a central runtime coordinator

Every player computes **the same deterministic press-owner** from the same game state:
- candidates: eligible non-GK agents;
- cost: estimated time-to-ball + stamina penalty + defensive-exposure penalty + role weight;
- tie-break deterministically by player ID.
- winner actively presses; others cover threats / lanes / support.
- exception: when a clear imminent goal threat is in the box, DEF may engage and MID covers.

This is *emergent coordination*. No sixth agent call, no chat dependency, and no shared-memory contention. Different snapshots may occasionally disagree; if timestamps differ, don't claim atomic coordination.

## Observation → decision → legality → application

For each tick log (with sensitive payload redacted):
1. role/team/side, ball state confidence, own stamina;
2. top three candidate actions and heuristic scores;
3. chosen action, reason tag (POSSESSION_SHOT, PRESS_OWNER, COVER, etc.);
4. validator pass/fail, latency, whether fallback was invoked;
5. action application and later outcome if reported.

The published [agentic_fc](../agentic_fc) code implements deterministic offline evaluation and format checks. It does not itself create an AWS Harness or deploy a Runtime.
