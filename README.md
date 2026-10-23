# Agentic FC — No Human in the Loop

## Latest: H2 research and complete prompts (2026-10-23)

**[Начать с полного H2-разбора на русском](research/v2/README.ru.md)** — tactics, model settings, advanced features, evidence corrections and rollout plan.

**[Five complete H2 Harness prompts](research/v2/prompts)** · **[Harness settings](research/v2/harness-settings.json)** · **[Executed scenario results](research/v2/results/scenario_results.json)** · **[Reproducible laboratory](research/v2/decision_lab.py)**

**Live experiment history (2026-10-23):** [A0/H2.1/H3 prompts, setup hashes and Fitness investigation](research/v3/README.ru.md). A0-M1 reached verified 5/5 Fitness after scrimmage-session reset and a MID tool restriction. A winning strategy remains to be established by live match evidence.

H2 lab: 20 named checks, 2,000 mirrored scene pairs, 20,000 validated commands, 10,000 mirror checks and 10,000 player-order checks. These are **synthetic policy tests, not AWS matches or LLM benchmarks**. No win rate, live model latency or tournament improvement was measured. H2 and later prompt bundles were subsequently trialled in AWS; see the dated live investigation below.

**Corrections to historical v1 documents below:** the current public Cup page does not establish the previously asserted hard one-second deadline. Participant workshop material reported five seconds; actual event timing must be verified. Nova 2 Lite currently does not support native Bedrock Structured Outputs; Haiku 4.5 supports them via bedrock-runtime. Prompt-only Harness does not automatically acquire structured schema enforcement by switching models. Use H2 source notes for current conclusions.

Run the new independent laboratory:

```sh
python research/v2/decision_lab.py
```

---

Research, tactics, prompts and a testable football policy for the **AWS Agentic Football Cup** (5v5).

> **Status:** A live team of five **AgentCore Harness** agents exists independently in the AWS workshop. This repository contains **offline policy prototypes, research and prompt variants**. It has **not** been deployed to AgentCore; tests here do **not** prove live match performance.

## Historical v1 material

| Goal | File |
|---|---|
| The findings from three supplied matches | [01-findings](docs/01-findings.md) |
| Architecture and decision flow | [02-architecture](docs/02-architecture.md) |
| Tactical playbook and thresholds | [03-tactics](docs/03-tactics.md) |
| Model choice, Memory, Gateway, Observability | [04-models-and-services](docs/04-models-and-services.md) |
| Experiment design and acceptance criteria | [05-experiments](docs/05-experiments.md) |
| Multi-round adversarial design review | [06-self-review](docs/06-self-review.md) |
| Safe workshop deployment | [07-deployment](docs/07-deployment.md) |
| Earlier prompt candidates | [prompts/harness](prompts/harness) |
| Historical sources (see H2 corrections) | [sources](docs/sources.md) |
| Original offline controller | [agentic_fc](agentic_fc) |
| Original local tests | [tests](tests) |
| Earlier developer implementation brief | [prompts/CLAUDE_CODE_TASK.md](prompts/CLAUDE_CODE_TASK.md) |

## Primary decision

Keep the working Harness team as **baseline A0**. Do not switch live ARNs until the new candidate has verified real input/output handling, local checks, five Fitness PASS and controlled practice results. Changes in a shared team coordination contract should be tested as a consistent five-role bundle; model changes should be a separate factor.

**Hypothesis:** disciplined press selection + complementary forward roles + state-aware pass/shot decisions outperform unconditional pressing. These are hypotheses, not proven tournament rankings.

## Runtime strategy

Deterministic state extraction and candidate generation, a bounded model choice, and software validation/serialization. If the event requires LLM decisions on every invocation, retain a genuine model choice rather than deploying the standalone deterministic laboratory. Optional deterministic fast paths require rule confirmation. No unbounded tool chain on the critical path.

CLEAR_OVERRIDE deliberately delegates to built-in engine behaviour; it does not guarantee the player stands still or holds a position. Do not issue team-wide RESET from an individual role. Log observed facts, candidate IDs, action outcome and latency, not private model reasoning.

Neither the original Python package nor the H2 laboratory is a live Bedrock/Strands integration. Reuse the official AWS entrypoint and validate the real event payload before integrating.

## Original offline tests

Python 3.10+, standard library:

```sh
python -m unittest discover -s tests -v
python -m agentic_fc.demo
```

## Source-of-truth order

1. A real captured invocation of **this** tournament and actual application of the action.
2. Current event's **AgentCore/Harness** instructions.
3. Official sample code and fixtures, checked for version compatibility.
4. Older coaching/strategy notes.
5. Our explicit heuristics and estimates, never described as calibrated probabilities.

## Safety and scope

Public repo. **Never commit team codes, AWS credentials, private game traces, account-specific ARN/account IDs or personal information.** Use synthetic fixtures. Verify IAM scope and workshop restrictions before deployment. Avoid running BOTH legacy and CDK Gateway deployers; they create separate resources. The live team remains unchanged by these GitHub commits.

## Reference implementation

Official AWS source: https://github.com/aws-samples/sample-ai-possibilities/tree/main/agentic-football-sample-agents

Cup information: https://agenticfootballcup.com/
