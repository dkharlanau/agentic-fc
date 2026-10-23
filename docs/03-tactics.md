# 03 — Tactical playbook: Adaptive Compact Counterpress (ACC)

**Recommendation for first experiments:** compact back line + one active presser + staggered forward pair + value-of-possession decisions. Press bursts rather than a five-player chase.

## Shape and phases

~~~mermaid
stateDiagram-v2
  [*] --> Neutral
  Neutral --> Ours: confirmed possession by our team
  Neutral --> Theirs: confirmed opponent possession
  Neutral --> Loose: ball free
  Ours --> Theirs: loss of possession
  Theirs --> Ours: recovery
  Theirs --> Loose: loose ball
  Loose --> Ours: controlled
  Loose --> Theirs: opponent recovers
  Ours --> Protect: late lead
  Theirs --> Chase: late deficit
  Protect --> Neutral: lead gone
  Chase --> Neutral: score level
~~~

Attack shape: GK protects own goal, DEF offers safe outlet, MID is connector, FWD1 attacks depth, FWD2 provides width or cutback option. Do not force fixed locations; adjust to ball side, opponents, stamina, phase and team orientation.

Defensive shape: GK on goal line, DEF blocks central route / marks top threat, MID is first or second presser, one FWD pressures from front, other closes passing lane and preserves transition outlet.

**Only one main presser** by default, optionally two on a strong press trigger with enough stamina and coverage. Do not use universal "PRESS whenever opponent has ball". High press drains stamina.

## Choosing pressing owner

Each eligible outfield teammate receives a *cost*, not a fake probability:

~~~
cost_i =
  0.55 * normalized_distance_to_ball
+ 0.20 * stamina_deficit
+ 0.20 * cover_penalty_if_player_leaves_role
+ 0.05 * role_bias
~~~

This is a starting heuristic, not a calibrated model. Press-owner = lowest cost (tie -> lowest playerId). DEF incurs a higher cover penalty near own goal; GK not eligible except emergency within goal box. Press only when the ball status is opponent-held or a confirmed free ball can be challenged; otherwise support.

## Ball carrier: compare alternatives

For a player with **confirmed** possession:
- Candidate shot: distance (2D!), **opening angle formed by two goalposts**, blocker lanes, keeper offset, own shooting skill if supplied, current pressure, score/time.
- Candidate passes to each *eligible teammate*: teammate advancement in attacking direction, lane clearance to teammate, distance, receiver pressure, passing skill, receiver stamina.
- Candidate dribble: reachable open space within own role limits and low tackle risk.
- If none is clearly superior, favour safe possession / built-in AI over blind SHOOT.

**Never claim 82% successful pass** unless a success probability has actually been calibrated against observed outcomes. AWS Gateway functions are hand-tuned heuristics; they use the key 'success_probability', but outputs are *uncalibrated scores*.

### Example ranking (illustrative, not a universal rule)

~~~
Shot score 0.54 | pass to FWD2 score 0.62 | dribble 0.41 => PASS FWD2
Shot score 0.81 | pass to MID score 0.48 | dribble 0.33  => SHOOT
Unknown possession => don't issue on-ball commands; cover or CLEAR_OVERRIDE
~~~

The player may still prefer taking a moderate shot when trailing near full time. Don't hardcode "shoot only if unmarked" — that can lead to zero shots against good defence. Introduce utility bias based on match context.

## Position specialisation

| Role | On ball | Off ball | Never by default |
|---|---|---|---|
| GK | distribute to safe outlet | track ball and shot line, protect goal | roam into midfield |
| DEF | safe forward/diagonal pass | shield goal, second defender, mark most dangerous attacker | follow opponent to far corner |
| MID | choose best pass, selective shot | press if designated, support triangle | spend entire game in PRESS_BALL |
| FWD1 | direct shot / penetrating pass | stretch into high-value space | track deep without a reason |
| FWD2 | angle/cutback/cross shot | different lane from FWD1, support | mirror FWD1 exactly |

## Stamina policy (exploration settings)

If raw stamina is fractional, try these *experimental*, non-universal bands:
- >= 0.70: permit short sprint for pressing/runs, if action value warrants it.
- 0.40–0.70: sprint only for recovery into a dangerous zone or decisive breakaway.
- < 0.40: reduce voluntary sprinting, maintain lanes/short passes.
- < 0.20: preserve emergency defence/goal saving, avoid chase on opponent half.

These are only candidate thresholds. Verify the *actual* runtime field and stamina regeneration in multiple traces. Opponent pressure/lastAction matters more than a single isolated threshold.

## Dynamic mode switches

- Early 0–0: balance pressing and shape; do not burn everybody's stamina.
- Leading: suppress risky long shots, avoid more than one committed pressing player.
- Trailing with little time: accept shots from moderately weaker positions and increase *coordinated* pressure.
- A recent loss of possession in attack: short counterpress if cover exists; otherwise recover defensive shape.
- Strong opponent keeper outside position: elevate shot opportunity score; do not automatically shoot from the touchline.

Mode selection must include **hysteresis** and minimum dwell time to prevent oscillation between ATTACK and DEFEND every tick.

## Hard match failures to test

1. HOME/AWAY flip must mirror all tactical coordinates.
2. Same agentId_N on opposing teams must not create two "ball carriers".
3. Bad or missing velocity must not crash the policy.
4. A free ball near GK must not drag GK far from goal.
5. Low stamina must not trigger unbounded high-press loops.
6. FWD1/FWD2 must not both choose the same support target unnecessarily.
7. Invalid target player ID / duration / aim must be rejected by validator.
8. CLEAR_OVERRIDE should be used intentionally, not interpreted as failed output.
