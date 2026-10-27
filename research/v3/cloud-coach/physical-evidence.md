# Observed game behavior, 27 October 2026

These are sampled private game inputs and owned decision logs, not Unity footage.
The public file deliberately omits raw states and identifiers.

## Units and limits

Players use raw x/y, while the ball's ground plane is x/z; ball y is height.
Observed current stamina is 0–1. Initial goalkeeper locations establish a stable
reference for normalization, not exact goalposts. Ball positions can extend past
player extrema, and a later match can enlarge the observed envelope. Never turn
an observed maximum into a surveyed field dimension.

Continuous open-play samples are roughly two game-seconds apart. Reset periods
can advance wall time/tick while gameTime is frozen; exclude those transitions
from velocity or fatigue calculations. Sparse observations can miss kicks,
contacts, saves and complete possession changes.

One conceded-goal sequence in the second outlet trial had a free incoming ball
moving at approximately 15.37 raw ground units/s, followed by a goal/reset only
0.18 game-seconds later. This illustrates why a reactive command arriving on the
next two-second decision cycle could be too late. It does not establish the
shot's launch power, exact goal line or which goalkeeper action would save it.

## Finishing evidence

Across four completed pre-finishing game projections, no FWD5 sample met both
baseline possession and close-shot geometry. The new empty-goal exception changes
one projected decision only. Projection coverage is not the full FWD5 request
stream and absence of sampled opportunities is not proof none occurred.

In the first finishing trial, an actual FWD5 CENTER/0.8 SHOOT was emitted at
13.60 game-seconds. At15.60 the ball was held and the baseline returned control;
at17.58 the sampled player state was SHOOTING and the ball was free; a goal was
observed at18.00. The intervening possession/override changes prevent a clean
claim that the explicit command caused that goal. Eight team goals do not become
eight successes of the one new rule. Native command validity is a different test.

No evidence yet isolates a causal power→speed or aim→accuracy curve. In particular,
a low observed rolling speed several seconds after a command is not launch speed.
Do not infer that multiplying the power parameter is legal or useful.

## Documentary disagreement

Read on27October2026:
- [AWS sample forward implementation](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-sample-agents/ai-team-strands-balanced/ai-fwd2/src/main.py)
  lists power0–1, CENTER and corner aim values, and stance1Attack/2Defend.
- [AWS coaching reference](https://github.com/aws-samples/sample-ai-possibilities/blob/main/agentic-football-coach/kiro-football-coach/content-reference/en/game-mechanics.md)
  instead labels stance1Defensive/2Attacking and describes timing/coordinates
  unlike some current observed inputs.

These are live main documents, not a pinned authoritative game-server implementation.
The conflict is a reason to retain validated behavior and test actual application,
not to reverse the team's stance enum on the strength of one document.

## Report integrity

Own runtime commands and portal per-role/command columns disagree. In the first
finishing match, an owned SHOOT exists while the displayed own command column
contains none. Generated prose also describes CLEAR_OVERRIDE as ball clearance.
That command releases control to built-in AI. Do not follow the report's advice
to use RESET or derive tactical causes from its prose. Preserve final score as a
separate observed outcome and verify each additional metric's attribution.


## 27 October 22:46 UTC: sampled pre-goal speed asymmetry

Across15recordedPracticegames (first root game has no fulltrace),39home goals
and14away goals were observed. Last pre-goal openplay snapshot shows a freeball
for19home and11away goals. Maximum positive x velocity in those19home samples
is4.471232;10of11away freeball samples have |vx|13.7–15.37, one3.68. These are
raw game-coordinate velocities, not measured launch power or metres/second.
All11away freeball pre-goal samples precede scorechange by0.10–0.58game seconds,
shorter than the typical2second decision interval. GoalkeeperJump is already
present in several cases: adding a late reactive cloud instruction is not proven
to help. Sparse and outcome-selected samples can bias this comparison. Some
positive-direction freeball samples outside scoring moments exceed8, so there is
no established universal4.5speed cap. Direction does not identify the kicker.

Official AWS sample forward still specifies SHOOT power0–1, matching the signed
workshop page inspected21:03. Do not blindly use100 or equate command intent with
launch. A separate maxpower1.0 diagnostic can preserve the earlier0.8 finisher's
exact narrow ownership/open-goal gates. Its response schema and goal count alone
will not establish physical power mapping. Raw episodes retained privately.
