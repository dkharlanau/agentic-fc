# Five real games, 24 October 2026

Four original M8 roles plus deterministic FWD2 revision7/source8b31760,
formation1-1-2. Normal stance mode, diagnostic disabled. Five games unchanged.

| Opponent | Score | Shots | Possession |
| --- | --- | --- | --- |
| KERON FC | 1:2 | 6:9 | 48% |
| Octopus | 3:2 OT | 5:5 | 61% |
| Couch Potato United | 1:0 | 12:0 | 23% |
| Amber Horns 2 | 3:1 | 4:5 | 38% |
| Apocalypse | 1:0 | 5:2 | 47% |

4W/0D/1L, goals9:5, shots32:21, 12points,2.4points/game. No scoreless games,
two clean sheets. Largest win accounts for3/9goals; without it3W1L,6:4goals.
Table104→109games,177→189points,137:94→146:99goals exactly reconciles.
Rank stays17; AllCash at599points/262games. All five HOME, uncontrolled opponents.
The same baseline action policy across cohorts06/07/08 totals8W1D2L,22:7,
25points/11games. This is not a controlled comparison or proof against leaders.

## Execution and latency

All five reports show100%success. Own-labelled role latencies range2–1509ms,
with per-match averages1109,80,1145,892,505ms. Models/configuration did not change.
The opposite-labelled FWD2 remains73–81ms while four positions are2–4ms.
These are portal labels, not established physical/model attribution. AI Overview
contains contradictions (for example advice to consolidate a losing team's lead);
its explanation is not independent evidence.

Exact own FWD2 sessions:405responses, zero model calls, zero geometry failures.
Five initial malformed bootstrap states released control safely. CPU medians
0.4009–0.5427ms, worst1.2966ms. All400well-formed rows usedstance, noneprobe-wide.
A prior native warm full request measured105.0ms median; CPU is not end-to-end.
Replacing a model cannot remove this FWD2 overhead because there is no model call.
It remains unknown which service/network/framework contributions dominate.

Commands: {"CLEAR_OVERRIDE": 199, "SET_STANCE": 187, "PASS": 9, "INTERCEPT": 5, "PRESS_BALL": 5}. Reasons: {"MALFORMED_POSITION": 5, "UNKNOWN_POSSESSION": 113, "ROLE_SUPPORT": 54, "ENGINE_RESTART": 75, "KEEP_SHAPE": 133, "NO_SAFE_OUTLET": 6, "SAFE_OUTLET": 9, "NEAREST_FREE_BALL": 5, "SINGLE_LOCAL_PRESS": 5}.
No model-generatedSHOT decisions; one observed ownShootAtGoal in third game
shows built-in action is not the same thing as an emitted command. Shot-distance
claims remain unverified. No broader role/model changes are justified by the
report latency alone.

## Tactical review and next bounded candidate

We scored first in all five, based on visible commentary and goal timeline.
KERON reversed1:0to1:2; Octopus reversed1:0to1:2before our3:2OT recovery.
Other three leads held. This is a transition/lead-management question, not proof
of goalkeeper failure. FWD2 energy late medians1.00/.967/.360/1.00/.118 vary;
last game ends0but stillwins. Fatigue is real in some games, not a universal
explanation of losses. Screenshots show deep forwards in one defended phase and
crowding in others, but do not establish a frequency or causal contribution.

One next candidate: HOME FWD2 off-ball passing support with nonsprinting,
bounded movement when team possession and frame are known. Keep four roles,
models, formation, ownership guards, and on-ball shot/pass logic unchanged.
Do not replace all five with experimental code. FWD2 HOME physical movement was
supported by two consecutive diagnostic intervals before the owner prohibited
further Practice; AWAY remains unverified and must keep baseline behavior.
Candidate not implemented/deployed yet. Native contract andFitness precede a
five-real-game trial; no Practice/Benchmark. Reject malformed/unassigned movement
or geometry failure; compare points, scoreless games, goals conceded, late energy.
Rollback: currently deployedrevision7stance. One favourable cohort is not enough
to call any setup final or guarantee tournament qualification.

## Recovery and quota guard

Current portable archive was rebuilt and all9sources match8b31760; SHA verified.
[Recovery](../../../fast_path_v2/RECOVERY.ru.md) includes pinned dependencies,
source hashes, normal mode, originals and rollback. New-account recreation still
needs live validation. Private raw states/ARNs/IDs stay ignored under.local.

Owner requires quota checks between games; atremaining<=5% stop new starts,
finish in-flight work and verify GitHub checkpoint before finalization. Remaining
20%at20:39UTC. Time window still ends02:38:51UTC25Oct, no newmanualgamesafter02:28:51.

Sources: [cohort08](../ranked-batch-08.json), [own audits](cohort08-audits.json),
[control gate](../fwd2-control/outcome.json), [earlier latency](REPLICATION_AND_LATENCY.md).
