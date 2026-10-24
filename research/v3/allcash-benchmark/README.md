# AllCash benchmark and fixed pitch-reference experiment

Started 24 October 2026 under the renewed 6–8 hour goal. The owner now requests
three-match cohorts. AllCash is the competitive benchmark, not a known model or
implementation blueprint. Its report latency is preserved in benchmark.json.

One change: separate fixed goal proxies from moving goalkeeper positions in the
isolated fast FWD2. In a counterfactual sequence based on the sanitized live-50
frame, the previous executor changes ROLE_SUPPORT to UNKNOWN_GEOMETRY solely
because keepers leave their initial positions. The corrected policy preserves
its validated reference in that session. Fresh unknown geometry and ambiguous
possession still release control. Current keeper lateral position only affects
shot aiming. Goal proxies remain approximate, not surveyed goalposts.

Local: 9 unit tests including mirrored observed-frame mutations, cross-session
isolation, fixed shot distance and uncertain ownership; 26 decision cases; 10000
CPU timings. These are not game wins or AWS latency. Native sequence adds moved
keepers and ambiguous ownership after calibration. Native/Fitness/Practice are
required before a stable three-ranked-game block. Original M8 is the rollback.

Prediction: lower UNKNOWN_GEOMETRY rate and preserved role support when keepers
advance. Competing explanation: unresolved possession still dominates; stance
control is less useful than engine AI; low latency alone does not improve play.
Reject on invalid binding, unsafe shot, failed Fitness, or lack of verified
useful physical execution. Do not promote based on synthetic checks alone.
Do not change prompts/models/formation/other players alongside this trial.

Telemetry investigation: original AWS Runtime log groups contain many telemetry
entries but sampled application session records cover the Fitness drill only;
no exact CypherForce/AllCash record was matched. This corrects the earlier
incomplete search scope, but still does not prove those agents were never called.
The Workshop explicitly supports both Harness and Runtime ARNs. Report counters
and opponent architecture remain unverified; do not automatically swap teams.

Private raw logs and session bindings stay in .local in local/CloudShell storage.
Public reports contain aliases and aggregate measurements only.
