# Matched loss review, 28 October 2026

Owner renewed cloud work at 05:03 UTC: understand defeats and make improvements.
This review does not renew the separately blocked max-power AWS deployment.
The installed five remain the selected L02B control, not retired Baseline/M11.
Last actual readiness: 03:10 UTC Fitness 5/5, exact five bindings, AWS READY.

## What the comparison rules out

Compare the same HOME Practice opponent and selected policy: Total Attack 5:0,
2:1, then 2:3. See `matched-control.json`. Snapshot counts are not time-weighted.

- MID stamina below .25: 16/61, 8/60, 3/59 full open-play snapshots.
- MID–protected FWD4 distance below one raw unit: 17/61, 16/60, 8/59.
- Therefore blanket stamina reduction or separation cannot be justified as the
  explanation for the latest defeat. These problems may matter in individual
  episodes, but were not more prevalent in this loss.
- No `NO_SAFE_OUTLET` MID decision occurred in the 59 loss snapshots. The earlier
  emergency-clearance candidate would not address these observed decisions.

## Episodes, not a fabricated single cause

Latest loss score changes: 25.960403, 37.900677, 71.939940 game-seconds.
The last available pre-goal samples are about 1.780, 1.940 and .180 seconds
before those changes. Exact launch/contact is missing for the first two.

At 29.980495 MID requested a recycle pass to DEF. That is not enough to blame the
37.900677 goal on this pass: at 33.900585 own FWD4 was again near the held ball,
then at 35.960632 opposing FWD5 was dribbling near it. Holder IDs alone are not
team-qualified proof; these are proximity/action observations, not complete
pass or turnover tracking.

Before 71.939940, the ball was near an opposition dribbler in their backfield at
69.740310; at about 71.760 it was free near our goal with vx about -15.22. Similar
fast return occurs in the 2:1 win at about 90.857→91.037 (vx about -13.90).
A new cloud GK command after that last sample cannot reliably arrive in .18s.
The missing launch interval prevents identifying the kicker or blaming power.

The defensive research target is the route BEFORE the fast return, including
possession loss and unopposed launch. Do not equate pre-goal velocity with shot
power, and do not tune GK from goal-selected frames alone. No new tactical
policy is proven superior by this review.

## Actual code repair

Both uninstalled finishing wrappers used parsed stamina, whose legacy parser
replaces missing/invalid values with 1.0. Reproduced: missing, null, text and
boolean stamina could enable an `EMPTY_GOAL` shot. They now require the actual
HOME FWD5 raw numeric stamina in .5–1.0 before the small-world exception.
Unknown input preserves the original baseline command. The parser and installed
baseline are unchanged. This is a candidate safety repair, NOT an explanation
for historical defeats or demonstrated scoring improvement.

The old max-power archive eb2f3d36 and its historical receipts remain unchanged.
It predates this repair and must NOT be deployed as repaired code. Build a new
archive with new source/hash and repeat all admission gates if deployment is
specifically approved. No new AWS writes or matches occurred in this review.

## Reusable inspection and tests

`analyze.py` constructs observed score-transition windows from private traces.
It rejects mixed frames/observer teams and score resets, deduplicates exact
captures, preserves unknown stamina and reports actual gaps separately from the
bounded eight-second episode window. Detailed inputs/outputs must stay in
`.local`; never publish raw player snapshots.

Run: `python -m unittest tests.test_loss_review tests.test_fwd_finish tests.test_fwd_power`
Full aggregate suite is `python -m unittest discover -s tests`.
Synthetic tests establish tool/safety behavior, not better play. Keep exact
policy/opponent/side when comparing, and retain losses as well as wins.

Final local checks: 217 aggregate tests PASS, 17 focused loss/finishing tests
PASS (7 loss-tool tests plus5 per wrapper), diff whitespace check PASS. Boundary
review verified .5/1 inclusive and invalid inputs returning unchanged baseline.
All979 valid open-play trace snapshots have finite0–1 FWD5 stamina; the repaired
bug is therefore not observed in this dataset. No native/Fitness gate was run
against the revised candidate. Existing deployed readiness is not its admission.
