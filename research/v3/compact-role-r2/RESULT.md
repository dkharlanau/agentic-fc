# Real-game latency test and fast FWD2 pilot — 24 October 2026

**No tournament upgrade was adopted.** Original M8 was restored and fresh Fitness
passed5/5 at18:29UTC. Five compact prompt candidates were updated, tested and
rejected before Harness deployment. An isolated deterministic FWD2 passed native
and Fitness gates, won one Practice, and lost one incoming ranked game; it was
unregistered after its latency/usefulness targets were not demonstrated.

The10ms target was **not achieved for a full AWS response or verified in a game**.
Submillisecond decision compute must not be presented as end-to-end response time.
There is no validated winning foundation-model selection from this experiment.

## Real matches and exact account reconciliation

| Group | Setup | Opponent | Side | Own score | Shots | Report role latencies, GK/DEF/MID/FWD1/FWD2 |
|---|---|---|---|---|---|---|
| Planned batch05 game1 | M8 | LFC | HOME | 0:2 | 8:6 | 242/139/273/256/137ms |
| Planned batch05 game2 | M8 | CypherForce Hotshots | HOME | 0:2 | 1:7 | 12610/12311/7733/13031/12615ms |
| Incoming after pause | M8 | Octopus | AWAY | 1:2 | 9:6 | 80/77/75/78/80ms |
| Incoming during Practice | Four M8 roles + fast FWD2 | AllCash United | AWAY | 0:2 | 5:9 | 83/84/86/82/82ms |
| Separate Practice | Four M8 roles + fast FWD2 | The Benchmark FC | HOME | 1:0 | 6:5 | 603/765/923/774/755ms |

[Batch05](../ranked-batch-05.json) ended at**2/5**, under its critical-error
exception. CypherForce showed0reportedcommands and11660ms average latency across
all five roles. Original Fitness passed5/5 again; exact match DEF log lookups
returned no events. The cause is unresolved, not proved to be model thinking,
throttling, cold start, or any one agent. Its100% Success counters do not prove
useful timely execution. The normal LFC defeat alone did not stop the cohort.

Fresh table before:15th,164points,94P54W2D38L,123:84. Fresh after saved
18:29:25UTC:15th,164points,98P54W2D42L,124:92. All four real losses reconcile
exactly:4games,0points,+1goalfor,+8against. Practice is excluded. The two incoming
games are separate from the planned cohort. AllCash was the current table leader;
its match overlapped Practice without a manual request. This contaminates a clean
serial comparison. No game was interrupted, no extra matchmaking was started,
and no model probes ran during the observed Practice.

Aggregate real results across **mixed setups**:0W0D4L,1:8goals,23:28shots.
These small uncontrolled groups do not establish a causal penalty for either setup.
Octopus also received an observed human coach instruction. AI Overview narratives
were not used as causal evidence; the user's angled-run observation remains an
observation, not a verified attribution to Haiku or GK.

## Updated prompts and actual foundation-model comparison

Five role files reduce conflicting shot instructions and state possession,
central cover, role support and a single presser explicitly. All remain
**rejected candidates**. Unchanged inputs and the same FWD2 prompt were compared
with four real Bedrock models, interleaved by case. Nine synthetic situations
include both sides, clear/blocked shots, possession ambiguity, stale context,
wrong binding, teammate support and low stamina. Expected outputs were never
sent to models. This was a FWD2-only screening gate; the other four new prompts
were not invoked after that gate failed. All36labels were independently
recalculated locally.

| Model | Strict command + decision gate | Full Converse median | Maximum | <=10ms |
|---|---|---|---|---|
| Nova2Lite | 0/9 | 571ms | 702ms | 0/9 |
| Haiku4.5 | 0/9 | 1478ms | 2533ms | 0/9 |
| Sonnet4.6 | 3/9 | 1548ms | 3077ms | 0/9 |
| NovaMicro | 1/9 | 441ms | 532ms | 0/9 |

[Full replies and usage](model-screen.json), [runner](evaluate.py),
[prompt hashes](manifest.json). Failures include Markdown/explanatory output,
missing/wrong duration, stale ownership and poor shot choices. Sonnet passed the
most cases but did not qualify for deployment. Micro was faster but failed the
gate. Direct Converse timings are not native Harness or game-server timings.
In the LFC report Haiku was our fastest role at137ms, so a claim that Haiku alone
caused that loss is unsupported.

## Deterministic fast executor — a different architecture

The owner requested10ms. [fast_path_v2](../../../fast_path_v2/) removes all
per-tick model calls. Its code resolves ownership, filters shots/passes, selects
one local presser and uses role support. This is **not** a faster LLM, weight
training, a learned cross-match policy, or demonstrated tournament superiority.
A separate FWD2 Runtime reused the existing execution role and code bucket.
Original Harness configs and IAM were not changed. All source was pushed before
native deployment. Latest deployed source is`b99bf77`; private receipts preserve
artifact/source hashes and exact bindings. The unused Runtime/artifact remain
in AWS; no match sessions were stopped or deleted.

Local checks:7unit tests;26synthetic decision cases, including an actual sequence
of old inputs followed by ambiguous ownership. The10000-call local measurement
includes deserialization, selection and serialization; [results](fast-local-eval.json)
record the actual CPU distribution and hashes. These are not hosted latency data.

Native stages are retained separately:

- Initial:18/18 valid; warm median108.38ms/max121.139ms; cold2891.241ms.
- Restart STANCE revision:20/20 valid; warm median106.044ms/max121.085ms.
- Restart MOVE revision:incomplete native validation after9recorded probes due
  an import error in the checking script. Its own native session was stopped;
  the script was fixed and the full run repeated. It is not a22/22 pass.
- Final:22/22 valid, including own-half nonsprinting restart targets on both sides;
  warm median105.055ms/max178.934ms, cold2870.557ms;0/21warm calls<=10ms.

[Initial native replies](fast-native-eval.json),
[final native replies](fast-native-v4-eval.json). Full body/SSE was consumed before
stopping the clock. Each native session was explicitly stopped in cleanup.

First portal Fitness:4/5, FWD2 inactive on0/1ticks. Exact own logs showed
CLEAR_OVERRIDE at KICK_OFF. Second:4/5, same active-command failure; logs showed
new-build SET_STANCE. These valid commands did not satisfy the active check.
The final revision moves to an own-half restart position only in the observed
full-size XY frame with verified keeper anchors. Small/unknown frames do not
receive invented world-coordinate movement. It passed fresh portal Fitness5/5,
then the single Benchmark Practice was completed.

## Match audit defeats a misleading positive interpretation

[Matched Runtime decision audits](fast-game-audits.json) use the exact portal
record's own team/position session, not the different Unity viewer ID. They store
sanitized audit fields/commands only, not raw input, credentials or resource IDs.

| Actual own FWD2 audit | Practice win | Incoming AllCash loss |
|---|---|---|
| Replies | 62 | 75 |
| Compute median / p95 / max | .392/.456/.516ms | .404/.469/.983ms |
| CLEAR_OVERRIDE | 59 | 35 |
| SET_STANCE | 3 | 38 |
| PASS / SHOOT | 0/0 | 2/0 |
| UNKNOWN_GEOMETRY | 39 | 1 |
| UNKNOWN_POSSESSION | 19 | 21 |
| Per-tick model calls | 0 | 0 |

The Practice win mostly delegated FWD2 control to engine AI. It does not validate
the new close-shot or passing policy in physical play. Two safe-pass selections
in the real match demonstrate some decision activity, not successful completion
of both passes. Report totals/role latencies do not cleanly match these audits;
no automatic inversion of report team columns or proof of wrong-player control
is asserted. The report credited the Practice goal to GK1; it is not attributed
to the new FWD2 or to its model. Reported755ms is not replaced by the logged .516ms.

## Decision and recovery

Reject promotion:full<=10ms was not demonstrated, own useful action coverage was
low, and one Practice win/one uncontrolled incoming defeat cannot show strength.
Restore original Haiku FWD2; retain Nova2Lite on the other four roles, formation112,
original13/19/15/16/14 role versions, no Memory/tools and history10. Fresh restored
Fitness5/5 was saved18:29:20UTC. Final API readback confirmed all five original
prompts/models/tools/history/memory settings unchanged from the pre-test snapshot.
The pilot was unregistered and its confirmed own Fitness session was stopped.

The one next correction, **not implemented/deployed here**, should investigate
why a trusted per-session pitch reference still leads to frequent geometry
rejection. The code caches a keeper reference but also checks current goalkeeper
locations, so keeper movement is a specific hypothesis to test. Preserve unknown
possession safety; never force a pass or shot merely to improve active-command
counts. Require observed-frame fixtures, native contract, Fitness and a separated
Practice before another live cohort. Original M8 remains a fallback, not a proved
optimal or tournament-winning configuration.

The [official AFC page](https://agenticfootballcup.com/) describes a one-second
agent budget and two-second decision interval. These public design claims do not
prove this workshop build's timeout implementation or explain its report counters.
The supplied10ms target is stricter and remains unmet. AWS [model availability](https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html)
is not a football quality or latency ranking.
