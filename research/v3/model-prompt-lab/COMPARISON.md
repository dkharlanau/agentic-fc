# Offline model/prompt comparison — 25 October 2026

155 archived responses; **zero new inference calls**. 109 full responses are regraded; 40 selector commands are reconstructed; six FWD1 format results rely on the saved full-message audit. The latter receipt intentionally omits full assistant text.

Validity = saved command schema (or the selector index contract). Usable = valid AND agrees with the scenario’s tactical label. Labels are hypotheses, not physical football quality. p50/p95 use type-7 interpolation; n is small and there is one response per case, without independent repetitions. The 20 selector rows comprise eight underlying scenarios with cyclic option orders.

## Full recorded groups

| Prompt | Role | Model | n | Valid | Usable | p50 / p95 ms | Timing boundary |
|---|---|---|---:|---:|---:|---:|---|
| compact-r2 | fwd2 | haiku | 9 | 1/9 | 0/9 | 1478 / 2151 | Converse request wall |
| compact-r2 | fwd2 | micro | 9 | 3/9 | 1/9 | 441 / 523.6 | Converse request wall |
| compact-r2 | fwd2 | nova2 | 9 | 1/9 | 0/9 | 571 / 678 | Converse request wall |
| compact-r2 | fwd2 | sonnet | 9 | 4/9 | 3/9 | 1548 / 3009.4 | Converse request wall |
| schema-clean | fwd1 | haiku | 3 | 2/3 | 2/3 | 1397 / 2946.8 | reported Playground |
| schema-clean | fwd1 | nova2 | 3 | 3/3 | 2/3 | 655 / 717.1 | reported Playground |
| r1-v1 | def | nova2 | 3 | 0/3 | 0/3 | 874 / 1093.6 | Converse request wall |
| r1-v1 | fwd1 | nova2 | 5 | 0/5 | 0/5 | 628 / 710.8 | Converse request wall |
| r1-v1 | fwd2 | haiku | 5 | 0/5 | 0/5 | 1388 / 2493 | Converse request wall |
| r1-v1 | gk | nova2 | 4 | 0/4 | 0/4 | 736 / 856.5 | Converse request wall |
| r1-v1 | mid | nova2 | 4 | 0/4 | 0/4 | 632.5 / 869.5 | Converse request wall |
| r1-v2 | def | nova2 | 4 | 1/4 | 0/4 | 536 / 761.3 | Converse request wall |
| r1-v2 | fwd1 | nova2 | 6 | 1/6 | 0/6 | 490 / 663.75 | Converse request wall |
| r1-v2 | fwd2 | haiku | 6 | 6/6 | 2/6 | 1660.5 / 4147.25 | Converse request wall |
| r1-v2 | gk | nova2 | 5 | 1/5 | 1/5 | 511 / 694.4 | Converse request wall |
| r1-v2 | mid | nova2 | 5 | 1/5 | 0/5 | 536 / 725.4 | Converse request wall |
| r1-v3 | def | nova2 | 4 | 1/4 | 0/4 | 799 / 1105.9 | Converse request wall |
| r1-v3 | fwd1 | nova2 | 6 | 1/6 | 0/6 | 725.5 / 1136.25 | Converse request wall |
| r1-v3 | fwd2 | haiku | 6 | 1/6 | 1/6 | 1436 / 1498.5 | Converse request wall |
| r1-v3 | gk | nova2 | 5 | 1/5 | 1/5 | 617 / 685.4 | Converse request wall |
| r1-v3 | mid | nova2 | 5 | 1/5 | 0/5 | 653 / 691.8 | Converse request wall |
| selector+tactics | fwd1 | micro | 20 | 20/20 | 20/20 | 1116 / 2787.35 | Harness full stream wall |
| selector+tactics | fwd1 | nova2 | 20 | 20/20 | 20/20 | 2061 / 4651.4 | Harness full stream wall |

## Prompt revisions on the SAME 21 cases

Five stale-context cases added in v2/v3 are excluded here to preserve paired case coverage. Calls were historical sequential runs; timing changes are not controlled causal effects.

| Role / model | Revision | n | Valid | Usable | p50 / p95 ms |
|---|---|---:|---:|---:|---:|
| def / nova2 | r1-v1 | 3 | 0/3 | 0/3 | 874 / 1093.6 |
| fwd1 / nova2 | r1-v1 | 5 | 0/5 | 0/5 | 628 / 710.8 |
| fwd2 / haiku | r1-v1 | 5 | 0/5 | 0/5 | 1388 / 2493 |
| gk / nova2 | r1-v1 | 4 | 0/4 | 0/4 | 736 / 856.5 |
| mid / nova2 | r1-v1 | 4 | 0/4 | 0/4 | 632.5 / 869.5 |
| def / nova2 | r1-v2 | 3 | 0/3 | 0/3 | 462 / 595.2 |
| fwd1 / nova2 | r1-v2 | 5 | 0/5 | 0/5 | 467 / 529.8 |
| fwd2 / haiku | r1-v2 | 5 | 5/5 | 1/5 | 1589 / 4259 |
| gk / nova2 | r1-v2 | 4 | 0/4 | 0/4 | 475 / 610.45 |
| mid / nova2 | r1-v2 | 4 | 0/4 | 0/4 | 516.5 / 650.75 |
| def / nova2 | r1-v3 | 3 | 0/3 | 0/3 | 793 / 1122.4 |
| fwd1 / nova2 | r1-v3 | 5 | 0/5 | 0/5 | 658 / 1129.8 |
| fwd2 / haiku | r1-v3 | 5 | 0/5 | 0/5 | 1457 / 1499 |
| gk / nova2 | r1-v3 | 4 | 0/4 | 0/4 | 630 / 688.05 |
| mid / nova2 | r1-v3 | 4 | 0/4 | 0/4 | 652.5 / 671.7 |

## Decisions and missing coverage

- GK/DEF/MID: no matched multi-model screen on current prompts. The three prompt rewrites do not qualify. No model recommendation by role can be inferred from FWD2 results.
- FWD1 current M8 prompt: Nova2 has 3/3 valid, 2/3 usable; Haiku 2/3 valid, 2/3 usable. Three cases do not justify switching.
- FWD1 selector: Micro model p50/p95 = 259/372 ms; Nova2 = 393.5/507.8 ms. Full Harness p50/p95 = 1116/2787.35 vs 2061/4651.4 ms. Maxima 32054 and 32247 ms are retained, not dropped as presumed cold starts.
- Selector facts include heuristicScore, option reason and a tactics mode that the instruction directly maps to actions. 20/20 measures rule-following, not independent tactical quality. Constant index0 already passes 12/20. Future selector tests must remove answer hints and permute options (see existing decision_eval.py permutation_cases).
- FWD2 compact screen: Micro is fastest, but only 1/9 usable; Sonnet 3/9; Nova2 and Haiku 0/9. Current FWD2 is deterministic and none of these is a justified replacement.
- Stale-context PASS repeats in DEF/MID/FWD1 in both r1-v2/v3 survive as syntactically valid mistakes. A prompt guard is a testable hypothesis, not a demonstrated fix to the live M8.
- Fast invalid replies do not count as good latency. results/comparison.json includes usable-only latency, evaluable-decision denominators and the original stricter policy-gate results.
- All unmeasured role/model/prompt cells remain not_measured with null percentiles in the coverage matrix. New 100-case suite has NO model results.

Sources, source/prompt hashes, per-case recomputed failures, quantile definition and all coverage cells: [comparison.json](results/comparison.json). Replay: `python3 research/v3/model-prompt-lab/lab.py`.
