# Fixed pitch reference: first ranked cohort

The later [replication and latency diagnosis](REPLICATION_AND_LATENCY.md) adds
1W1D1L and two scoreless games. Read both before judging the setup.

24 October 2026. Deployed source `8747a88`, fast FWD2 revision5; original M8
GK/DEF/MID/FWD1 and formation1-1-2 unchanged. This remains a provisional setup.

| Ranked opponent | Side | Score | Shots |
| --- | --- | --- | --- |
| WKS MUCHOBÓR WROCŁAW | HOME | 4:0 | 8:2 |
| ForzaMilan13 | HOME | 2:0 | 8:0 |
| Amber Horns 2 | HOME | 4:0 | 13:2 |

Three wins,10:0goals,29:4shots,+9points. Account98→101games,164→173points,
124:92→134:92goals reconcile exactly; no additional incoming result in this
interval. Rank15→16 while competitors also played. AllCash remains first:
569→581points,250→256games. Matchmaking chooses opponents randomly; there is
no observed selector to demand a game against AllCash.

Gates:9local tests,26decision cases,28/28native,Fitness5/5. Separate Practice
against Benchmark won4:0,6:2shots; excluded from ranked totals. Full native warm
median103.465ms,max130.076ms. The10ms full-path target is **not achieved**.

## What the correction established

Pinning validated goal proxies avoids using advancing keepers as moving goals.
Practice previously had39/62UNKNOWN_GEOMETRY responses; now0/84. The three ranked
exact-session audits contain241responses with **zero UNKNOWN_GEOMETRY**,
zero model calls, per-game CPU medians0.548/0.409/0.552ms,max1.294ms. Three
malformed initial connectivity inputs safely release control. CPU time is not
transport time. Own audit aggregate:118CLEAR,114STANCE,3PASS,4PRESS,2INTERCEPT.
Unknown possession still occurs62times; we do not infer ownership from proximity.

## Limits and decision

The three report tables show the fast-four-plus~80ms pattern under the opponent
label, although our own fast FWD2 exact-session audit is deterministic. Team
attribution remains unresolved; do not swap labels automatically or infer the
opponent's models. Amber's37Reset labels are not attributed to our fast executor.
AI Overview and coach prose are not independent causal evidence.

All three games are HOME against nonleaders. Historical M8 also beat Forza2:0.
Three wins support another unchanged three-game replication, not a claim that
the correction caused all wins. C02shot selection remains unmeasured; no direct
fast FWD2SHOT occurred. C03defensive concern is not exposed by this zero-concession
sample. Keep the same five registrations and formation; no next policy/model
change yet. Rollback is original FWD2v14 with the same other four M8 roles and
freshFitness5/5 if a critical failure occurs.

Sources: [cohort06](../ranked-batch-06.json), [ranked audit summaries](ranked-audits.json),
[Practice audit](practice-audit.json), [native gate](native-v5.json),
[benchmark snapshots](benchmark.json). Raw sessions, bindings and screenshots
remain private in ignored `.local/`; reproducible audit code is in
`fast_path_v2/audit.py`. Original agents/models were not retrained.
