# Result: bundled prompt-only candidate rejected before deployment

24 October 2026, 17:29 UTC. Original M8 remains the operational lineup. No
candidate Harness was created or registered; no candidate Fitness or ranked
match was started. The five-role prompt experiment reached its model gate and
failed. The five-game protocol was therefore not activated.

## Actual model evidence

Three revisions were run through Bedrock Converse from visible AWS CloudShell,
using each role's assigned model: Nova 2 Lite for GK/DEF/MID/FWD1 and Haiku 4.5 for
FWD2. All cases are explicitly counterfactual states derived from a saved Fitness
fixture. These are real inference responses, not simulated model outputs.

| Revision/source | Full decision + output contract | Median request wall time | Maximum |
|---|---:|---:|---:|
| [v1](model-eval-v1.json), f2b34be | 0/21 | 711 ms | 2,509 ms |
| [v2](model-eval-v2.json), a2887e0 | 3/26 | 573 ms | 4,706 ms |
| [v3](model-eval-v3.json), 9310c75 | 2/26 | 696 ms | 1,501 ms |

73 evaluation calls plus one format canary and six isolation probes were made.
v1 often returned fenced JSON and omitted duration. v2 often returned an empty
array; several Haiku outputs shot from a prohibited distance or through a block.
v3 added an explicit schema but still produced fenced JSON and unsafe decisions.
Even stripping fences would leave tactical/parameter failures. Do not weaken the
gate to obtain a passing score. The checker reproduces all saved v3 labels.

The format canary returned exactly `{"ok":true}`. A focused Nova FWD1 probe
returned the empty array with an empty, explicit, absent, or explicitly explained
unlockedCommands field. Thus empty unlockedCommands alone did not explain that
failure. The original M8 prompt produced valid command JSON in that same isolated
case, but chose a shot from too far away by this candidate's proposed criterion.
This does not establish M8's score over the full suite or a measured in-game shot
distance. A facts-only probe resolved team/player/possession correctly but used
Markdown, so correct fact extraction alone did not guarantee the output contract.

## Context is a measured input risk, not an established cause of match losses

Five additional cases supplied four previous state/answer pairs, then an
ambiguous current owner. v2 input tokens grew from 1,977–2,203 without history
to 5,629–6,059 with history. DEF/MID/FWD1 repeated a prior pass; GK/FWD2 released.
The same three stale passes persisted in v3. These are small adversarial samples.
Fresh-state responses were already poor, so history cannot be named the sole
cause. The lower v2 median is dominated by invalid two-token empty outputs and
is not a performance improvement. No claim about live p95 latency is justified.

## The cited fast opponent actually lost this game

Fresh primary portal report, No Human in the Loop HOME versus ForzaMilan13:

| Metric | Our team | ForzaMilan13 |
|---|---:|---:|
| Goals | 2 | 0 |
| Shots | 9 | 0 |
| Possession | 32% | 68% |
| Reported command count | 369 | 13 |
| Reported average latency | 818 ms | 2 ms |
| GK/DEF/MID/FWD/FWD latency | 612/905/911/639/899 ms | 3/3/2/2/2 ms |
| Reported success | 100% each | 100% each |

The source contains AI-generated commentary; none of its causal explanations is
adopted. Reported RESET2 and no SHOOT despite9shots are additional attribution
limits. The response-time counter, command count and physical action are not
interchangeable. Opponent code/model and the exact latency measurement boundary
are unknown. A 2ms counter does not demonstrate a better model or better football.

The latest observed leaderboard in this turn was15th,161points,93P53W2D38L,
121:84goals,+37. Since the original15:39snapshot89P155pts, four background games
are visible: Amber Crests2 win0:1 AWAY, Zorja loss0:2 AWAY, Juja loss0:3 HOME,
ForzaMilan13 win2:0 HOME. This reconciles +4P/+2W/+2L/+6pts/+3GF/+5GA.
They were not candidate trials. The recent20-game page showed7W1D12L; its mixed
configurations do not represent a stable M8 cohort.

## Latency decision and next discriminating test

Measure complete usable command arrival, then acceptance and physical execution;
time to first token and an average report counter cannot substitute for these.
The current workshop's exact action deadline still requires direct verification.

The next defensible candidate is a short, constrained decision path: code resolves
identity/possession and filters unsafe receivers/shots; the model chooses among
remaining actions; code serializes the command and rejects stale/invalid choices.
Keep only a compact observation summary, not a transcript of large stale states.
Measure fresh versus history-loaded inputs and repeated identical-prefix inputs,
with positive controls that must still attack and take a clear close shot.
This is a proposed next experiment, not an implementation or a proven winning
architecture. The previous R1 selector's poor five-game result remains contrary
evidence; do not blindly restore it or assume code guards solve team movement.

AWS documentation checked during this iteration:

- [Prompt caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)
  can reduce repeated-prefix work on supported models. Verify actual cache-read
  metrics; no hit or improvement is guaranteed. Do not lengthen a prompt merely
  to meet a cache threshold. Cache changes were not deployed.
- [Latency-optimized inference](https://docs.aws.amazon.com/bedrock/latest/userguide/latency-optimized-inference.html)
  lists selected model families; our Nova2Lite and Haiku4.5 are not in that page's
  support table. Do not blindly add the optimized setting.
- [Nova2 extended thinking](https://docs.aws.amazon.com/nova/latest/nova2-userguide/extended-thinking.html)
  is off by default. Enabling expensive deliberation every tick is not an
  evidenced latency fix; no such setting was enabled.
- [Structured-output prompting](https://docs.aws.amazon.com/nova/latest/userguide/prompting-structured-output.html)
  recommends a schema. Our v3 tested a schema *in prompt text*, not Bedrock's
  separate grammar-constrained outputConfig API or a guaranteed validator.

Exact original M8 remains available through the unchanged recovery bundle.
Six local package tests passed. No AWS resource/registration/model/history,
formation, IAM, heartbeat or computer power setting changed in this iteration.
