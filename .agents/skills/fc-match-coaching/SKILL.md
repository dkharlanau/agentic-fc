---
name: fc-match-coaching
description: Run and analyze bounded Agentic FC coaching experiments using exact lineup, Fitness, native-response and match-state evidence. Use for this repository's authorized football work, not unrelated AWS administration.
---

# Coach from observed behavior

Read AGENTS.md, current HANDOFF.md, EXPERT_COACH.md and the latest COACH_REVIEWS.md.
They own the current operator, environment, deadline, reserve, release permission
and block cadence. This skill does not grant AWS, match, credential or publication
permission. Preserve a running block and any newer owner restriction.

## Admission and rollback

- Verify the actual portal, current private active-match receipt and exact five
  saved bindings. UI FWD4 is playerId3; FWD5 is playerId4. Identical agentId values
  occur on both teams. Never infer the team from that ID alone.
- While a match is running, observe only: no probes, deployment, role changes or
  test-session cleanup that could touch game sessions.
- Before changing a role, retain the exact prior binding and artifact/configuration
  identity. Isolated native checks must use newly created owned session IDs;
  save their identity privately before invocation and stop only those sessions.
- Check complete response bytes, command identity, adversarial ownership/geometry,
  repeated inputs, cold and later calls. Passing a response schema is not Fitness.
  Fresh Fitness and prematch readiness are separate gates. A rendered saved field
  is not proof of persistence: close/reopen or read the saved detail view.
- Keep one bounded tactical hypothesis per comparison. Respect the current block
  size. Ordinary losses do not authorize mid-block tuning. Record partial blocks
  and genuine readiness failures rather than quietly resetting the series.
- Restore and recheck Fitness when a candidate fails its stated admission or
  retention criteria. A preserved old artifact is not automatically ready.

## Evidence chain

For a proposed improvement, distinguish:
input → chosen command → full delivered response → observed movement/contact →
match result. Missing links stay unknown. A projected MID snapshot fed to FWD5 is
an offline counterfactual, not an authentic replay of FWD5's request stream.

Use actual sampled episodes to ask who held the ball, who offered a useful pass,
who covered the goal after a loss, and what changed before a shot. Separate facts,
calculations and hypotheses. A submitted PASS is not a completed pass; SHOOTING
state is not a shot count or known pre-shot energy. A goal soon after a command
does not by itself prove that command caused it.

Keep one-sided, two-game and bot comparisons qualified. Compare like opponents,
sides and configurations where possible. Retain losses and unusually large wins.
Historical ranked matches and current Practice are separate populations.

## Non-obvious implementation traps

- CLEAR_OVERRIDE releases an override; it does not kick or clear the ball. RESET
  affects teammates. Do not adopt generated report advice to issue RESET.
- Portal command/role columns have disagreed with owned runtime logs. Verify
  attribution before deriving passing, shooting, goalkeeper or latency conclusions.
- Raw small-world players use x/y while ball ground coordinates use x/z. Keeper
  anchors are a tactical reference, not surveyed goalposts or pitch boundaries.
  Observed extrema do not prove exact field size. Do not import documentary
  distances, stance enums or timing constants without resolving contradictions.
- Complete SDK wall time includes network and startup. Internal compute and portal
  Fitness0ms are different measurements. If client connection setup is measured
  separately, label that boundary and retain initial failures; never subtract
  unexplained delay or prewarm agents to manufacture a cold-start PASS.
- Match log collection must be bounded by that match's actual start and end.
  Preserve pagination and deduplicate events. Managed SDK logs may wrap the
  diagnostic string inside another JSON message; parse both layers, do not mistake
  startup/CPU telemetry for decision evidence.
- An unavailable Unity/WebGL view is not gameplay footage. Use explicitly labeled
  sampled-coordinate reconstructions, preserve gaps, and do not bypass browser
  restrictions or switch to a prohibited computer.

## Reuse existing tools

Use tests/ for contract and synthetic safety checks; the relevant package's
builder for exact source/archive verification. For raw snapshots, use
research/v3/cloud-coach/trace/render_snapshot.py rather than building another
viewer. Keep inputs and renders in ignored .local/. Native wrappers and collectors
need current private bindings; never put credentials, identifiers or raw game
states into this skill or public examples.

Record a compact decision in COACH_REVIEWS.md and sanitized, linked receipts in
research/v3/. Update HANDOFF.md with what is actually installed, checks performed,
limitations, exact rollback and next executable step. Do not turn test counts or
successful releases into claims of stronger football.
