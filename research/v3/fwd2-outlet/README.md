## Decision after five real games

Not promoted: 2W/3L, goals5:5, shots24:32, two scoreless games. The previous
stance cohort was4W/1L, but opponents differ. Return stance; retain this source
and artifact only as a reproducible rejected experiment. See ../ranked-batch-09.json
and audits.json. 406 exact own responses,66 outlet moves,zero model calls.

# FWD2 passing outlet candidate

Opt-in FWD2_MODE=outlet; defaultstance remains the rollback. Only HOME FWD2,
known own-team possession, off-ball and validated keeper-reference movement.
Other roles, on-ball decisions, formation and models remain unchanged.

Target lies behind the ball, clipped between midfield and attacking support;
two lateral options prefer the side opposite the other forward. Reject occupied
receiving points; rank space, passing corridor, separation and travel distance.
No sprint. Near the target or outside the validated conditions usebaseline.
These distances are tactical heuristics, not optimal or calibrated probabilities.

Hypothesis: more usable passing outlets and less crowding without losing goals
or exhausting FWD2. Prior five-game control4W1L,9:5goals,2.4points/game is preserved.
Energy and opponent quality vary; no causal improvement is claimed beforehand.

Local13tests passed, including baseline scenarios, ownership, HOME/AWAY, restart,
role and occupied-target guards. Native34/Fitness5 required before five REAL games.
No Practice/Benchmark per owner. AWSrevision8READY/native34/34/Fitness5/5; realfive-gamecohort09started.
Rollback mode=stance withsource8b31760/revision7; save native receipt and new
source separately. Recovery builder can use this artifact manifest; for recreation
setPLAYER_ID=4,FWD2_MODE=outlet only when deliberately restoring this experiment.
The existing fast_path_v2/artifact.json remains the proven baseline manifest.
