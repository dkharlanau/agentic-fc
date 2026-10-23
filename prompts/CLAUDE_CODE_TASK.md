# Implementation brief for Claude Code / Kiro

Repository: dkharlanau/agentic-fc.

Goal: win through reliable state-aware decisions, NOT maximum count of PRESS/SHOOT. Avoid editing live AWS resources until explicit approval.

## 1. Read before coding

Read docs/01-findings through docs/07-deployment and inspect the official AWS sample: https://github.com/aws-samples/sample-ai-possibilities/tree/main/agentic-football-sample-agents/ai-team-strands-balanced . Reuse its streaming interface; do not invent game fields. Existing docs contradict on SET_STANCE and time limit.

## 2. Audit state contract

Ensure teamCode normalization; TEAM+playerId identity; duplicate agentId_N on both sides; UNKNOWN vs FREE; HOME/AWAY attack sign; fractional stamina vs static skills. Preserve velocity, lastAction and stats if available. Capture true traces and redact all live identifiers before any public commit.

## 3. Integrate Python policy

The included agentic_fc code is an offline deterministic controller. Adapt to a real BedrockAgentCoreApp + Strands Runtime using the official entrypoint and JSON streaming with one command per controlled player. Do not call it deployed. Preserve teamId from payload, never hardcode HOME. Add strict validation and a safe fallback. Individual agents never emit team-wide RESET.

## 4. Controlled model routing

For genuinely ambiguous choices with a remaining time budget, add one bounded Bedrock adviser call; never depend on a multi-tool chain during a hard 1-second deadline. Compare current Nova 2 Lite with Nova Micro/Lite/Pro on identical saved states. Measure P50/P95/P99 and valid applied commands before deciding position model mapping.

## 5. Tactical refinements

Test one at a time: press-owner assignment, defensive cover, complementary forward lanes, 2D distance and goal-post angle, keeper/blockers, pass-lane clearance, stamina bands, score/time modes. The four AWS Gateway scores are handcrafted heuristic estimates, not calibrated probabilities. Do not force pass or shot quotas.

## 6. Tests and release

Run: python -m unittest discover -s tests -v. Expand tests with fixtures and fuzzing: HOME/AWAY symmetry, duplicate IDs, absent fields, conflicting possession, invalid output, timeouts, wrong target. Then create CI workflow. NEVER commit real ARN, participant code, account ID, credentials or raw sensitive logs.

Keep current Harness A0 fallback. Deploy candidate B only after IAM permission, integration tests, five Fitness PASS and controlled matches across different opponent classes. Record versions and roll back portal ARN mapping on regression. Do not run Gateway CDK and legacy deployment scripts together.
