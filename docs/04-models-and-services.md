# 04 — Model routing and AWS special features

**Constraint:** Cup event site states ~2s decision cycle and a **hard 1s per-agent reply budget**. An older Game Mechanics coaching note states 500ms instead. Use live portal errors/traces as final authority. Success-rate=100% is not proof of sub-1s P95.

## Candidate models — not a ranking

| Model | Where to test | Tradeoff / reason |
|---|---|---|
| **Nova 2 Lite** | Current Harness baseline on existing players | User-observed reliable fitness and scores; per-position latency often 0.59–1.4s in 3 matches; test tails |
| **Nova Micro** | GK and simple DEF **in code-first Runtime with deterministic JSON** | AWS balanced sample uses it; fast but greater risk of strict JSON errors in Harness |
| **Nova Lite** | DEF and FWD2 candidates | AWS balanced code sample uses it; unknown live P95 here |
| **Nova Pro** | MID adviser for complex choices; only if latency fits | AWS sample uses on MID, but large model is not automatically faster/better under budget |
| **Claude Sonnet 4.6** | Offline tactic design, code authoring, red-team review | More complex reasoning; on-field latency may be unacceptable, measure before considering live |
| **Another available Bedrock model** | Only after same-state, same-prompt evaluations | Compare latency tails, schema validity, and decision regret, not marketing benchmark scores |

Official AWS balanced **code** sample uses Nova Micro GK/FWD1, Nova Lite DEF/FWD2, Nova Pro MID. This is a reference design, not an empirically proven winning five-model combination.

### Recommended model experiment

Keep current Nova 2 Lite Harness as A. For Runtime B, start with a **fast model** for ambiguous MID/FWD decisions only, while deterministic logic handles known cases and JSON. Never introduce a second model call on the default path. Do not treat "model remembers match" as a guarantee: session context, memory and tool permissions depend on integration and may reset.

Run the **same recorded situations** against each model, log P50/P95/P99, schema errors, chosen action and regret against accepted tactical rules. Only then assign models to positions. Stochastic decisions require repeated trials with identical input.

## Features: value per latency

| Feature | Could help | Drawback | Recommendation |
|---|---|---|---|
| Harness prompt-only | Fast to edit, no packaging | JSON non-determinism; no deterministic validation | Keep as baseline |
| Strands + Python Runtime | Safe serialization, state math, fallback | New deployment and IAM; must test real wrapper | Main competition candidate |
| AgentCore Observability | Traces show actual state/output/latency | Telemetry may lag; privacy | Enable for debugging |
| Gateway tactical MCP tools | Pass/shot/space/mark heuristics | Extra model-tool round trips; heuristic scores not probabilities | Port calculations **in-process** first; test Gateway separately |
| AgentCore Memory | Recent opponent tendencies | Provisioning, extra latency, stale history/session semantics | Compact bounded state first; not default |
| Multi-agent coordination | Press assignment, coverage, spacing | Five agents may see slightly different states | Deterministic shared rule from same snapshot |
| Lifecycle hooks | Deterministic guardrails if correctly configured | Extra infrastructure, uncertain overhead | Programmatic validator preferred |
| Coach/Shout | Live temporary adjustment, fast experiments | Public and may be ignored; confounds A/B trials | Keep for manual experiments only |

## Why the four AWS Gateway tools are inspiration, not ground truth

Official functions:
- calculate_pass_options: opponent proximity to a pass **segment** and distance penalty.
- evaluate_shot: goalkeeper position, blockers, distance; outputs an uncalibrated 'success_probability'. The code computes but **does not use** dy in an angle factor; cannot be trusted as calibrated xG.
- find_open_space: grid search for maximum distance from opposition. That may choose empty but **unreachable** or strategically irrelevant zones.
- get_defensive_assignment: ranking by proximity to own goal, ball and possession; not a full coverage/marking solver.

See sources. Valuable heuristics can be computed locally in microseconds rather than using Gateway calls every 2s. If tool access is a workshop goal, run separate controlled Gateway vs local-heuristic trials.

## Latency safety

Budget: 1000ms (according to 2026 Cup site), reserve time for parse, runtime, serialization and network. A model averaging 900ms may frequently be late. Use a measured deadline and don't invent wait guarantees. Default to bounded quick logic under pressure.

## Costs, permissions and cleanup

Workshop role likely cannot create arbitrary IAM resources. The current Harness uses pre-provisioned 'team-SolutionAccessRole-*'. The official Gateway CDK route creates IAM, Lambda, CloudFormation and Gateway resources; it may be denied in an event account. Read the specific IAM policy and obtain organizer approval before deploy. Avoid both legacy and CDK Gateway routes together; they create duplicates.
