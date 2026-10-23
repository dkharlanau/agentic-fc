# Agentic FC — No Human in the Loop

Research, tactics, prompts and a testable football policy for the **AWS Agentic Football Cup** (5v5).

> **Status (2026-10-23):** A live team of five **AgentCore Harness** agents exists independently in the AWS workshop. This repository contains an **offline policy prototype, research and prompt variants**. It has **not** been deployed to AgentCore; tests here do **not** prove live match performance.

## Start here

| Goal | File |
|---|---|
| The findings from three supplied matches | [01-findings](docs/01-findings.md) |
| Architecture and decision flow | [02-architecture](docs/02-architecture.md) |
| Tactical playbook and thresholds | [03-tactics](docs/03-tactics.md) |
| Model choice, Memory, Gateway, Observability | [04-models-and-services](docs/04-models-and-services.md) |
| Experiment design and acceptance criteria | [05-experiments](docs/05-experiments.md) |
| Multi-round adversarial design review | [06-self-review](docs/06-self-review.md) |
| Safe workshop deployment | [07-deployment](docs/07-deployment.md) |
| Copy-paste prompts for all five Harness positions | [prompts/harness](prompts/harness) |
| Source references and contradictory specs | [sources](docs/sources.md) |
| Executable offline controller | [agentic_fc](agentic_fc) |
| Local tests | [tests](tests) |
| Developer implementation brief | [prompts/CLAUDE_CODE_TASK.md](prompts/CLAUDE_CODE_TASK.md) |

## Primary decision

Keep the working Harness team untouched as **baseline A**. Do not switch live ARNs until:
1. You inspect real AgentCore input/output traces (HOME and AWAY).
2. The new implementation passes schema, possession, role, field-side, and fatigue tests.
3. It passes Pre-match Fitness with all five positions.
4. Paired practice matches show meaningful improvement and no severe regressions.

**Hypothesis:** disciplined press selection + two distinct forward roles + state-aware pass/shot ranking outperform unconditional pressing. These are hypotheses, not proven tournament rankings.

## Runtime strategy

- **Fast path:** deterministic state extraction, action prioritisation and JSON validation, with no model/network call.
- **AI path (integration target):** use a fast Bedrock model when the decision is genuinely ambiguous, bounded by the confirmed current event deadline. AI proposals are *advisory* and pass through the same validation; no unbounded tool chain on the critical path.
- **Fallback:** safe, legal single-player command; CLEAR_OVERRIDE deliberately delegates to built-in engine behaviour. No team-wide RESET from one position.
- **Observability:** log facts, candidate actions, selection reason, confidence category, latency and actual outcome when available.

The shipped Python package implements the **offline deterministic core**, not a live Bedrock/Strands integration. Its model hook remains an integration task: see [07-deployment](docs/07-deployment.md). The official AWS sample has a real Strands + AgentCore entrypoint, parsing and fallbacks. Use it as the integration base.

## Try locally

Requires Python 3.10+; only standard library for offline tests:

~~~sh
python -m unittest discover -s tests -v
python -m agentic_fc.demo
~~~

## Source-of-truth order

1. A real captured invocation of **this** tournament and successful live response.
2. Current event's **AgentCore/Harness** instructions.
3. Official sample repo code and fixtures.
4. Older coaching/strategy notes.
5. Our heuristics and estimates (never described as calibrated probabilities).

## Safety and scope

Public repo. **Never commit team codes, AWS credentials, private game traces, account-specific ARN/account IDs or personal information.** Use synthetic fixtures. Verify IAM scope and workshop account restrictions before deployment. Avoid running BOTH the legacy and CDK Gateway deployers; they create separate resource sets.

## Reference implementation

Official AWS source: https://github.com/aws-samples/sample-ai-possibilities/tree/main/agentic-football-sample-agents

Cup information: https://agenticfootballcup.com/
