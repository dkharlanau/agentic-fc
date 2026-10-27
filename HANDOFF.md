# Current checkpoint — L02B coaching cycle, 2026-10-27

Owner wants short iterations: one change/deploy,2–3 observed games, concise
coaching review, next improvement. Current block: one game with each benchmark
TotalAttack, Benchmark, FortKnox. This supersedes older five-game development
cadence. Watch real screen as user/coach. CLI/SDK preferred for AWS errors/deploy.
Stop starting work at10% remaining agent/Codex quota; last verified24% remaining.
No new agents, IAM expansion, automation or auto-merge.

## Current game and evidence

- Three-game GK block completed: TotalAttack1:0, Benchmark2:0, FortKnox5:0;
  3W,8:0,18:13shots. Sampled screen evidence, no physical pass census.
- New single change: FWD2 open-goal central shot, source5d3d13a, separateRuntime.
  Registered; freshFitness5/5 and all5exactbindings verified. OldFWD2 preserved for exactrollback.
  Local18testsPASS, native6/6 including2cold calls5321/3638ms; warm319–945ms.
- Next2Practice: FortKnox, TotalAttack; observe carefully, then top3 improvements
  requested by owner. Two-game cohort ready to start; use active-match.json for current status. Do not add outlet/clearance or
  prompt changes to this shot pilot. Plan research/v3/shot-stage2/plan.json.
- CUA readback open-goal-fwd2-readback.txt confirms newFWD2 binding. Other4 unchanged.
- Report attribution unresolved: ownedGK onlyCLEAR but report owncolumn GKDist.
  Internal GK/MID/FWD2 computation/flush mostly<1ms is not network latency.
  Audit:research/v3/stage2-gk-fast-cohort-audit.json. Harness game latency unknown.
- Private active-match.json is source of truth with fresh portal. No probes/settings
  while pending/LIVE. Raw frames/logs/IDs remain ignored .local/.

## Verified configuration

Actual freshFitness5/5,5commands100%active; exact5portalbindings read back before
firstgame. Fitness0ms mean is not game latency. Formation1-1-2.
- GK: separate fast_path_v2 Runtime PLAYER_ID0, source dcaf97c. Deterministic safe
  distribution with explicit ownership/lane; built-in goalkeeping otherwise.
  Holds own current position on validated full-size XY kickoff.14localtestsPASS;
  native originalHOME/AWAYdistribution2/2, own sessions stopped, finalAWSreadback.
- MID3: L02B original912 artifact plus restart_compat.py overlay0028079. Owner
  explicitly requested fixing repeated pre-match failure. One exact initial
  tick0/time0 positioning retry allowed within5s instead of1s; changed/intervening,
  third, late and open-play frames still release.13testsPASS. All other deployed
  module bytes unchanged (including original fastboot without local pass logger).
- DEF/FWD1/FWD2 remain original canonical versions. CanonicalGK13 and original
  L02B912 bindings preserved as rollback; require freshFitness after rollback.
- Current private bindings:gk-fast-final-bindings.json. Deployment receipts:
  gk-fast-r2-deploy.json and mid-retry5-deploy.json. This is GK plus a declared
  MID startup transport repair, not a pureGK causal comparison.

## Rejected approaches and queued questions

Micro model-only3/8 safety, G2prompt9/12 with AWAY errors: rejected. G3 delegate
allopenplay12/12 policy but actualFitnessfailed: no games. FastGK initialFitness
failed because FREE KICK_OFF producedCLEAR; misleading possession tip contradicted
ownedlogs. GK startup fix passed. MID repeats1.19/2.23/2.46s exceeded old1s window;
separate5s fix now passedFitness. Keep failures in keeper-stage2/results.json.

Owner observations: DEF2 skips forward passes; weak shots; opponent long shots;
high latency. FWD2 explicitshotpower0.8, FWD1prompt example0.9 is not measured
actualpower. Evaluate after3; maximumone next tactical change. Native cold3–33s
retained; SDKfull/modelmetadata/portalmean have different scopes. Command counts
are not physical passes/shots. ReportSOT often equals goals; semantics unknown.

Read EXPERT_COACH.md (coach-v1.0) and recent COACH_REVIEWS.md before/after block.
Worktree stage2-native-screen, branch codex/stage2-native-screen-20261027; main
checkout dirty, untouched. Draft PR9 attached, no merge. Commits dcaf97c/0028079
local; documentation/results uncommitted. Closed historicalcohorts:L02B10 7W3L,
M11stopped4 2W2L,Baseline2 1W1L,L02Bvisual2 2W/6:1. Never silently resume.
[Prior handoff archive](research/v3/handoff-history-before-gk-20261027.md) is history.
