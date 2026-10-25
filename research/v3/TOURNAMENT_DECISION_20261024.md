# Tournament decision — 24 October 2026

**Decision: retain A (M8) as the tournament fallback. Prepare exactly one next
experiment: B, formation 1-2-1 with the same five original Harness. Do not
adopt B from the existing single win.** No live matchmaking, model invocation,
AWS deployment, scheduling change or extension of the previous window was
performed in this bounded mission. The experiment below requires separate,
explicit authorisation and a new bounded execution window.

## Configuration and evidence boundary

The latest **recorded** live verification is 15:39 UTC on 24 October: M8,
1-1-2, original GK/DEF/MID/FWD1/FWD2 versions 13/19/15/16/14, Fitness 5/5.
GK/DEF/MID/FWD1 use `global.amazon.nova-2-lite-v1:0`; FWD2 uses
`global.anthropic.claude-haiku-4-5-20251001-v1:0`. Memory is disabled;
tools/allowedTools/skills are empty; history is 10. Experimental R1 and GK are
unregistered in that snapshot. This mission did not refresh the live portal.
Rank 14, 155 points and 89 matches are historical account counters, not a fresh
leaderboard or the size of the 80-report analytical dataset.

All five prompt hashes, five exported configuration hashes and the recovery
bundle hash were verified locally against the [manifest](final-setup-20261024.json).
No model, prompt, Runtime source or recovery request was changed. A documentation
inconsistency was corrected: the FWD1 bundle records sourceVersion **15**, the
original pre-memory role was 14, and the last restored role was 16. The
`baseline-m8` recovery profile explicitly disables memory. Version numbers are
resource-local history; hashes and requested settings define the configuration.

Sources: [matches](matches.json), [batches 01](ranked-batch-01.json),
[02](ranked-batch-02.json), [03](ranked-batch-03.json), [04](ranked-batch-04.json),
[shot analysis](shots-analysis.json), [saved prompts](schema-clean/),
[Runtime history](runtime-r1.json), coach-v1.0 and proposals-v1.0. Input source
was commit `fb826084b0bebdf54ee29491f7d8df69a81d2448`.
[Recomputed evidence](tournament-evidence-20261024.json) records exact source
hashes, membership, nulls, side strata and counter reconciliation. Live capture
order is not guaranteed match-start order; unattributed background games remain
separate from verified configuration cohorts.

The [official AFC site](https://agenticfootballcup.com/), checked 24 October,
describes a two-second decision interval and one-second response budget. It does
not confirm this team's 29 October event, its ranking/tie-break rules, or the exact
workshop build's timeout behaviour. Treat the date as provisional. Do not invent
controllable opponent selection, HOME/AWAY allocation or seeds.

## What changed in the results

| Recorded cohort | H/A | W/D/L | Points/game | Goals | Known shots; coverage |
|---|---:|---:|---:|---:|---:|
| Early M8, live28–38 | 11/0 | 10/1/0 | 2.82 | 19:2 | 94:18; 10/11 |
| Same early window plus next attributed M8 loss, live41 | 12/0 | 10/1/1 | 2.58 | 20:4 | 97:24; 11/12 |
| Mixed settings, live53–62 | 3/7 | 4/0/6 | 1.20 | 15:10 | 82:39; 10/10 |
| Stable original M8, live63–72 | 8/2 | 5/1/4 | 1.60 | 12:11 | 31:49; 9/10 |
| FWD1 R1v14, planned live74–78 | 3/2 | 1/0/4 | 0.60 | 5:8 | 24:22; 5/5 |
| R1v14 including incoming live73/79 | 3/4 | 1/0/6 | 0.43 | 6:11 | 34:30; 7/7 |
| Formation 1-2-1, live80, owner-ended partial batch | 1/0 | 1/0/0 | 3.00 | 1:0 | 6:6; 1/1 |

These are calculations, not causal effect estimates. The four batch account
deltas exactly reconcile with their recorded games. Batch04 remains **1/5**;
the four cancelled games do not become observations.

**HOME/AWAY does not fully explain the decline.** Recent M8 HOME PPG is 1.625
(4W/1D/3L, n=8), versus 2.818 in the early HOME window. Recent AWAY is 1.5
(1W/1L, n=2). Early M8 has no AWAY overlap, so a full side-adjusted early/recent
effect is not identifiable. Equal HOME/AWAY weighting gives recent M8 1.5625
and planned R1v14 0.5, but cannot control opponent difficulty.

**Opponent control is very thin.** The only shared opponent-name/side pairs
between early and recent M8 are Matrix_7 HOME and Singularity FC HOME: both
were wins in both periods, 6 points each period. Shots fell from 29:4 to 11:4,
without a points decline in those two pairs. Same names do not prove unchanged
opponent versions. The recent M8 and planned R1v14 blocks have **no shared
opponent names**. Pre-match opponent strength/rank and versions are unavailable;
no supported claim about performance specifically against strong teams is possible.

**Configuration changes and selection matter.** Live53–62 mixes five attributed
configuration labels plus three unattributed games. Its 7:0 win contributes
46.7% of our goals. Removing it only as a sensitivity calculation gives 8:10
goals and 1.0 PPG; it stays in the official result. Early success is not an
ongoing unbeaten run: include live41 when discussing the next attributed game.
Older original 1-2-1 reports (22–27,42,46) were 6W/2L, 2.25 PPG, but seven
were HOME, some included coaching, and opponents/report regimes differed.
They justify feasibility of B, not superiority over A.

**Anomalies do not explain everything either.** Excluding live69 only as a
sensitivity gives stable M8 1.78 PPG and 31:37 known shots. Excluding live66
and69 gives 2.0 PPG and 31:24. Neither exclusion establishes that the results
were caused by infrastructure, and neither replaces the official 1.6 PPG.
No regression with many covariates is fitted to these small, non-overlapping
groups. The defensible explanation is a mixture of opponent/side selection,
changed policies and unresolved execution effects, with residual match variance;
their individual causal contributions cannot be identified from these records.

## Four failure classes

| Class | Observed evidence | Mechanism to investigate | Competing explanation and falsifier |
|---|---|---|---|
| Attack starvation | Four stable-M8 losses have 4:40 shots; live66 and69 have zero own shots. Live66 still reports 53% possession. | GK/DEF outlet, MID reception and forward support may fail to form a usable progression chain; several players may press instead of offering an outlet. | Opponent pressure or missing/late overrides could cause the same result. Falsify the spacing explanation if eligible own possessions consistently have an available outlet and timely completed progression yet attacks still disappear. |
| Low opportunity conversion | Mixed53–62 lost four of eight shot-advantage games; planned v14 lost both of its two shot-advantage games. | Poor shot choice, lost ownership before command arrival, blocked lanes or an unchosen pass could waste possession. | Report semantics and opponent shot quality are unknown. Reject a shot-filter claim if event samples show close/open timely shots, or if fewer speculative shots also reduce goals/points. |
| Defensive instability | Stable M8 has three one-goal losses; v14 has four. Live75 led 2:0 and lost 2:3. | Loss of central cover after a turnover, duplicate press or unsafe outlet could expose the goal. | Quality of opponent finishes, fatigue, delayed decisions and GK positioning remain alternatives. Falsify the cover hypothesis if goal events show central cover intact. Final score alone cannot identify a GK defect. |
| Execution/latency | Live69 reports zero commands for both teams and 13,335ms own mean; unchanged Fitness passed and following games resumed normal counts. Live66 reports seven commands/1ms. | Missing or late delivery, fallback, wrong attribution or invocation differences. | Exact live69 DEF-log lookup returned no events, not a diagnosed root cause. Require matched request/output/receipt/player evidence; report averages alone cannot establish idling. |

The loss-selected shot totals locate episodes; they are not an independent
statistical proof that shot starvation causes defeat. A GK→DEF→MID→FWD funnel
cannot be computed: there is no complete possession/event chain for these M8
games. Future denominators must be **observed, eligible own-possession sequences**,
with successful receptions, turnovers and unobserved intervals retained. Command
PASS counts are not successful passes. Sample the same kind of possessions in
wins as well as losses, and use equal observation windows for each configuration.

Across all 78 complete reports, 512 own shots and 102 registered shots on target
are recorded; SOT equals goals for **both teams in every complete report**.
Live29 and72 are missing shot tables. In live53/55/57/59/60 there are reported
shots despite no reported own SHOOT command. The parser reads goals and SOT
from different table sections, so there is no direct goals→SOT assignment there.
We cannot call the remaining 410 shots misses, compute save percentage, estimate
xG or conclude that long shots always miss. No shot-distance/outcome pairs exist.

## Prompt, state and transport audit

* FWD1/FWD2 say shoot within approximately 25 units, then assign higher priority
  to close, clear-lane shots and safe passes. This is an ambiguous heuristic,
  not evidence that the model ignored the later priority. MID has a similar
  distance rule. Replacing 25 with another arbitrary number is unsupported.
* Captured Fitness uses a large 2D field (keepers near ±50, stamina100). One
  captured live AWAY state uses keepers near ±6, ball x/y/z and fractional
  stamina. In that live state, ball z corresponds to the player's second planar
  coordinate in the archived adapter. Raw 25-unit comparisons across these
  formats are unsafe. Exact goalposts and M8's actual interpretation are unknown.
* `agentId_N` repeats on both teams. The live50 fixture has a possession agent ID
  without a possession team; it is not unique identity. R1 derives a candidate
  from contact and motion, which is explicitly an inference. A mirrored fixture
  is an offline counterfactual, not physical AWAY validation.
* FWD/MID nearest-appropriate-press priorities have no shared tie-break rule;
  DEF separately says to press in its zone. Duplicated pressure is plausible.
  Conversely, multiple independent uncertainty decisions could leave nobody
  pressing. Neither has been established from recent M8 event sequences.
* GK prioritises a throw to the nearest teammate without explicitly ranking
  pressure/lane risk. The new synthetic marked-outlet cases are useful checks;
  they do not show this happened before a conceded goal. Do not swap GK on that basis.

| Execution link | Established | Missing |
|---|---|---|
| State → decision | Saved R1 inputs, audit decisions and build hashes; two sanitized observation fixtures | Recent M8 per-tick model input/output and invocation overrides |
| JSON → SSE | Archived native/SDK tests; generator emits the command array; prior native success once coexisted with portal NO_PARSE | Exact tournament receiver behaviour on every response |
| Server receipt → correct role | Fitness 5/5 at the saved checkpoint; own HOME FWD movement observed in two Practice07 intervals | Per-command acceptance/deadline records for recent M8, all roles and AWAY |
| Applied action → football benefit | Primary match scores; limited physical movement observations | Counterfactual benefit, systematic shot/pass completion and defensive event attribution |

R1 `modelLatencyMs` measures its model-call block. `totalLatencyMs` is assembled
inside `choose`, before `memory_sample`, wire transport and game application.
The entrypoint awaits the sampled Memory write **before returning the SSE
generator**; its configured connect/read timeouts are 2s/2s. Thus model p95
under one second does not prove end-to-end compliance. This is a code-path
observation, not a measured cause of v14 losses. M8 has Memory disabled and does
not execute this custom entrypoint. A faster model or asynchronous Memory rewrite
is consequently not the selected next experiment.

## Offline evaluation completed

[Fixture pack and audit](decision-eval-20261024.json), generated by
[decision_eval.py](decision_eval.py): **20 state cases, only two unchanged observed
inputs**, and 18 explicitly labelled counterfactuals. They cover HOME/AWAY,
ambiguous/conflicting possession, high press, compact block, turnover recovery,
low energy, GK/MID outlets, wrong role binding and malformed nested state.
Source hashes and mutation descriptions travel with the cases. State objects are
deduplicated by SHA-256; exact replay instructions are included in the file.

The archived R1 is exercised with a fake model; this is neither an M8 evaluation
nor new inference. Nineteen cases satisfy the declared narrow contracts. One
reproduces a defect: `players=null` raises an unhandled TypeError during audit
construction after the fake model returns. `ball=[]` safely releases control,
so it is not labelled a tactical failure. Wrong-role binding is rejected.
The malformed case was authored; no recorded match is claimed to contain it.
The R1 defect remains documented and unpatched because that candidate is
unregistered and is not the chosen experiment. Existing tests missed it.

The choice pack contains **50 orders: 48 genuine multi-option comparisons and
two forced singletons**, using all permutations rather than only the first
ordering. Constant indices0/1/2 each score24/48; first-PASS30/48,
first-SHOOT12/48, first-CLEAR0/48. None passes all comparisons. Clear-close-shot
cases prevent an always-pass strategy from appearing perfect. Future model input
contains raw synthetic state and indexed commands; expected tactic labels,
heuristic scores, reason tags, case IDs and answer keys must remain outside it.
No model has been run on this new pack. Its tactical preferences are declared
heuristics, not ground-truth optimal actions or proof of physical execution.

Five new evaluator/integrity tests pass. Also rerun: 19 existing Runtime tests,
four report-parser tests and six recovery tests with mocked AWS clients: **34
unit tests passed**. The separate adversarial audit's one finding remains visible;
34 passing unit tests must not be read as 20/20 Runtime robustness or fitness.

## Decision round and adversarial challenge

| Rank for use now | Path | Expected competitive value | Implementation risk | Verification cost / timing |
|---|---|---|---|---|
| 1 | A — keep M8 1-1-2 | Best supported available fallback; remaining weaknesses unresolved | Lowest; already preserved | Local integrity verified; fresh readiness required when actually returning to play |
| 2 | B — only 1-2-1 | Unknown upside: a second central starting position may improve outlet access and turnover cover | Low deployment risk, real tactical risk: one fewer forward and unchanged FWD prompts can override shape | One authorised five-game block plus minimal event capture; no deployment or new model needed |
| 3 | C — minimal tactical/reliability edit | No demonstrated defect in deployed M8 tied to results; speculative benefit | Prompt/coordinate changes can suppress attacks or misroute actions | Requires a captured failing M8 trace and matched output first; unsuitable as an unverified final-day edit |

**Select B as the only prepared experiment; keep A installed.** The intended
mechanism is central connection and cover, not a promise that two MID labels
create coordinated midfield behaviour. Formation may change only starting
positions; players3/4 retain their striker prompts. If observed movement immediately
collapses back into the old shape, the proposed mechanism is unsupported.

Adversarial review was a separate self-review pass, not an independent person
or an additional agent:

* B's historical win and older 6W/2L might be opponent selection/HOME advantage.
  They are feasibility evidence only. No five-game block can prove a global optimum.
* A's 1.6 versus v14's0.6 is not a causal ranking: no shared opponent names.
  However, v14 has no demonstrated competitive benefit warranting tournament risk.
* Strong-opponent capability is unknown without pre-match opponent strength.
  Do not relabel losing opponents “strong” after the result.
* A higher shot ratio or pass count can coexist with worse points. Efficiency
  and physical progression must support, not replace, competitive outcomes.
* R1's malformed-input defect and blocking Memory path are real engineering
  concerns but do not diagnose installed M8. They are not a reason to combine
  formation, model and Runtime changes.
* With five nominal calendar days until the unconfirmed target, reproducibility
  and a reversible test have more value than a new architecture. If authorisation,
  event rules, access or observation quality are missing, retain A and stop.

## Exact five-match execution and rollback protocol — NOT EXECUTED

**Experiment ID: `formation121-original-five-next5`.** This is a new block of
five, not a resumption or relabelling of the owner-ended 1/5 batch04. Live80
remains outside its primary result. No auto-resume or scheduled task is created.

1. Obtain separate explicit authorisation for this experiment and a bounded
   start/end window. Confirm actual event rules, ranking mode, response budget
   and permissible passive observation. Check for an active game; finish it
   unchanged. Never stop game sessions. If M8 has drifted, stop the experiment
   and record the mismatch instead of silently restoring other settings.
2. Capture a fresh leaderboard and all five bindings/models/prompt hashes;
   compare to the final manifest. Preserve private registration receipts. Keep
   Memory, tools, models, prompts and GK/FWD1 bindings fixed. Change only the
   portal formation from1-1-2 to1-2-1, save, reload, verify the displayed shape
   and require Fitness5/5 before any new match. No CloudShell deployment.
3. Count the **next five completed eligible ranked games** on that verified
   configuration, regardless of ordinary wins/losses or incoming/manual origin.
   Never select only favourable opponents or HOME games. Use serial matchmaking;
   do not start a new game while any is active. If an incoming game appears,
   record it, count it if eligible, and do not launch a parallel Practice/probe.
4. For each game record local report alias, side, opponent, pre-match strength
   if visible, initiation, confirmed configuration, result, nullable shots,
   critical failures and leaderboard reconciliation. No per-game tactical changes.
   Where passive data are available, sample a fixed opening60 game-seconds of
   open play for both teams: first three eligible own GK/DEF possession sequences
   (including wins), outlets/MID reception/turnover/attack outcome, and first
   three turnovers. Missing observations stay unknown. Capture every conceded
   goal/lead reversal when available. Do not extend a match or invoke diagnostics
   to fill a quota. Existing M8 has no equivalent event baseline: these samples
   can falsify B's mechanism but cannot prove improvement over A's progression.
5. Stop new starts at the authorised cutoff or after five completions. Ordinary
   losses do not stop or reset the block. On NO_PARSE, wrong-player/frame proof,
   invalid routing, or the severe zero-both-teams/high-latency symptom, pause
   **new** starts, allow any active game to finish, and inspect readiness between
   games. If unresolved or repeated, terminate as partial and restore A. An
   isolated low command count is flagged, not automatically called a failure.
6. Reconcile all account changes, including additional games. Compare to M8
   live63–72:16/10points,1.6PPG,1.2GF/game,1.1GA/game,4/10scoreless and
   two known zero-shot games among nine reports. Publish H/A strata, opponent
   overlap and missing-data coverage. Equal-side weighting is descriptive only;
   do not impute an absent stratum or discard a difficult opponent.
7. Predeclared conservative **screen**, not significance: below9points/5,
   more than2scoreless games, any known zero-shot game, more than6conceded,
   or a new confirmed execution failure does not qualify B for retention.
   The integer thresholds approximate or improve M8's observed rates; they
   are operational risk limits, not calibrated win probabilities. Missing shot
   tables/event evidence or no observations on one side make the verdict
   inconclusive. Even a9+point clean block only qualifies for a separately
   authorised matched replication; it does not establish superiority.
8. At the block boundary, **restore A by default**: the same five original
   Harness, formation1-1-2, save/reload, read back all bindings and obtain
   Fitness5/5. If a match is active, defer rollback until it finishes. Do not
   create resources for a formation rollback. For a future account reset use
   `python3 research/v3/recovery/restore.py --profile baseline-m8` as an offline
   plan; applying it needs the new authorised account/role and private receipt.
   Full five-role fresh-account restore remains untested.

The spacing hypothesis is falsified for this trial if central outlet availability
does not appear in the bounded observations, or sustained attacks/cover disappear
despite timely applied commands. If physical execution is unknown, the mechanism
is **unresolved**, not confirmed or falsified. No permission or replication is
inferred from elapsed time, Fitness, or a passing screen.

## Reproduce and hand off

Files changed in this mission:

* Added this decision/protocol, `decision_analysis.py` and
  `tournament-evidence-20261024.json` for reproducible cohort calculations.
* Added `decision_eval.py`, `decision-eval-20261024.json` and
  `test_decision_evidence.py` for the fixture pack, archived-R1 audit and evaluator tests.
* Updated `HANDOFF.md` and `COACH_REVIEWS.md` with the bounded decision; corrected
  export-version prose in `FINAL_SETUP.ru.md` and `final-setup-20261024.json`.

The five `schema-clean/` prompts, recovery bundle, `matches.json`, Runtime code
and four historical batch reports are unchanged.

Run from the repository root; no AWS credentials or network are required:

```sh
python3 research/v3/decision_analysis.py
python3 research/v3/decision_eval.py
python3 -m unittest discover -s research/v3 -p 'test_decision_evidence.py' -v
python3 -m unittest discover -s tests -p 'test_runtime*.py'
python3 -m unittest discover -s research/v3 -p 'test_report_parser.py'
.local/aws-20261024-sixhours/sdk-venv/bin/python -m unittest discover -s research/v3/recovery -p 'test_*.py'
```

The last command uses the existing local dependency environment; another Python
environment with recovery dependencies can replace it. Recovery tests mock the
AWS client even when their output says “ready and configuration verified”.
`decision_eval.py` exports only existing sanitized observations and labelled
counterfactuals. Raw private logs and access details remain outside Git.

Remaining unknowns: current live configuration/standings, actual tournament rules
and date, opponent strength/versions, M8 per-call end-to-end timing and action
acceptance, shot distance/outcomes, complete goal sequences, and physical AWAY
command validation. Mission ends with this decision, reproducible evidence and
the updated draft PR5; no further autonomous research loop is authorised.
