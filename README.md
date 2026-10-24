# Agentic FC — No Human in the Loop

## Latest: live experiments and portable recovery (2026-10-24)

**[Начать с полного H2-разбора на русском](research/v2/README.ru.md)** — tactics, model settings, advanced features, evidence corrections and rollout plan.

**[Five complete H2 Harness prompts](research/v2/prompts)** · **[Harness settings](research/v2/harness-settings.json)** · **[Executed scenario results](research/v2/results/scenario_results.json)** · **[Reproducible laboratory](research/v2/decision_lab.py)**

**Live experiment history (2026-10-23):** [A0/H2.1/H3 prompts, setup hashes and Fitness investigation](research/v3/README.ru.md). A0-M1 reached verified 5/5 Fitness after scrimmage-session reset and a MID tool restriction. A winning strategy remains to be established by live match evidence.

**Current AWS trial:** [M7 / 1-2-1 restored](research/v3/setups.json). Haiku 4.5 remains on FWD2, Nova 2 Lite on the other four roles; [schema-clean prompts](research/v3/schema-clean), empty tools, sliding history10 and disabled Memory are preserved. FWD1 v16 is behavior-identical to pre-Memory v14 and UI Fitness is5/5. The M9/M10 Memory/fresh-resource experiments are retained as unsuccessful live trials; native Memory writes worked, but live-match use was not established. **[Portable five-role recovery kit](research/v3/recovery/README.ru.md)** preserves actual AWS settings and safe creation receipts. [Six-hour run receipt](research/v3/run-20261024-sixhours.json).

**New code candidate:** [R1 bounded model selection Runtime](runtime_v1/README.md) has six passing offline core tests, an SDK streaming smoke check with fake clients, and a Linux ARM64 CodeZip manifest. It has not been deployed or validated live yet. It keeps a genuine Bedrock action choice while code enforces side/player identity and JSON; raw traces and resource bindings remain private.

The [prior M8 session receipt](research/v3/run-20261023-summary.json), [resumed-session receipt](research/v3/run-20261024-resume.json) and [side audit](research/v3/side-audit-20261024.json) distinguish later defeats and the HOME-only historical cohort. [Sonnet FWD1 probes](research/v3/fwd1-sonnet-probes.json) document rejected laboratory alternatives; no Sonnet model or candidate prompt was installed. [Possession probes](research/v3/possession-probes.json), [prompt probes](research/v3/prompt-readiness-probes.json), [direct FWD1 model probes](research/v3/fwd1-direct-model-probes.json) and [native canaries](research/v3/model-probes.json) document trial rationale and limits. [Routing probes](research/v3/routing-probes.json) retain rejected laboratory candidates and input-shape limitations; none of those prompt candidates replaced the saved role prompts. See [setup history](research/v3/setups.json) and [rendered report numbers](research/v3/matches.json).

H2 lab: 20 named checks, 2,000 mirrored scene pairs, 20,000 validated commands, 10,000 mirror checks and 10,000 player-order checks. These are **synthetic policy tests, not AWS matches or LLM benchmarks**. No win rate, live model latency or tournament improvement was measured. H2 and later prompt bundles were subsequently trialled in AWS; see the dated live investigation below.

**Corrections to historical v1 documents below:** the current public Cup page does not establish the previously asserted hard one-second deadline. Participant workshop material reported five seconds; actual event timing must be verified. Nova 2 Lite currently does not support native Bedrock Structured Outputs; Haiku 4.5 supports them via bedrock-runtime. Prompt-only Harness does not automatically acquire structured schema enforcement by switching models. Use H2 source notes for current conclusions.

Run the new independent laboratory:

```sh
python research/v2/decision_lab.py
```

---

Research, tactics, prompts and a testable football policy for the **AWS Agentic Football Cup** (5v5).

> **Status:** A live team of five **AgentCore Harness** agents is being operated in the AWS workshop. Prompt bundles and settings in research/v3 have been installed and their observed live reports recorded. Python policy prototypes and laboratories remain offline; their tests do **not** prove live match performance.

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

Public repo. **Never commit team codes, AWS credentials, private game traces, account-specific ARN/account IDs or personal information.** Use synthetic fixtures. Verify IAM scope and workshop restrictions before deployment. Avoid running BOTH legacy and CDK Gateway deployers; they create separate resources. Publishing this history does not deploy the offline Python controller; AWS prompt/configuration changes are recorded separately in research/v3.

## Reference implementation

Official AWS source: https://github.com/aws-samples/sample-ai-possibilities/tree/main/agentic-football-sample-agents

Cup information: https://agenticfootballcup.com/
