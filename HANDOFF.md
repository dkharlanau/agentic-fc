# Agentic FC — live continuation checkpoint, 2026-10-25

L02 native screens are complete on V2 and V1. Both failed the 1s first-call
gate: six of six first-session calls late on each platform, despite 224/224
valid full-contract replies. V1 headers consumed nearly the complete 1.28–1.34s
wall; application work was ~1ms and Python import/readiness 168–236ms. This
locates the delay before response headers, but not the exact platform/network
component. No Fitness, L02 binding, or candidate match. The current registered
baseline remains unchanged. Do not repeat this identical archive blindly.
Research evidence is in the adjacent research repository at
`research/v3/model-prompt-lab/results/mid-l02-native-screen-20261025.json`.

Batch17 is complete 5/5 on the unchanged registered baseline: Le Masia 2:0,
Amber Arcs 2 1:0, Agents United 0:0, Apocalypse 1:0, BlackEagle 2:0. Total
4W/1D/0L, goals 6:0, 13 points. Leaderboard reconciles exactly from #13 / 169
played / 305 points to #12 / 174 / 318, 104W/6D/64L, goals237:143. Stats exist
for four reports: 22:14 shots, 6:0 on target, own possession mean44.25% over
those four; Agents United report omitted these stats. All five opponents' command
reports show CLEAR 72–90%; this is a five-match description, not proven tactical
intent or success. Our report means are 84–786ms in four coherent reports; Amber
Arcs' 1ms fields conflict and are excluded. <=10ms not achieved. Two high-MOVE
matches ended draw/win and do not justify an automatic change. Full raw rows,
coverage, and cautious series analysis: `research/v3/ranked-batch-17.json`.
L02 remains rejected on V1/V2 cold-call gates; no candidate was installed.

# Agentic FC continuation

## Latest checkpoint — 2026-10-25, batch16 complete and opponent profiles

Batch16 is complete 5/5 on the unchanged live baseline: Gork ’n’ Mork Boyz 2:0, Ada 2:1, Shalqar United 5:0, Amber Arcs 2 2:1 in sudden death, FantasyFootball 0:1. The five recorded outcomes total 4W/0D/1L, 11:3, 12 points. Across reports: 37–7 shots and 11–3 on target. The first two recorded rows do not reconcile with the wider account snapshot (five match and 13 point delta); unmatched changes remain unattributed. Shalqar report: 16–84 possession, 18–0 shots, 5–0 on target; 474 vs 88 commands at 980 vs 16 ms team means. Their action mix was CLEAR 65/88 (74%), PASS 22/88 (25%), PRESS 1, and zero shots. Our role means were 577/1187/887/867/1278 ms. The low-possession, 5/5 on-target result is one observation, not proof of a repeatable advantage. Formation, pass completion, field locations and clearance effectiveness are unknown. Leaderboard: rank13, 169 played, 305 points, 100W/5D/64L, goals231:143. FantasyFootball row: rank39, 47 games, 99 points, 33W/0D/14L, goals60:36; it beat us 1:0 with 51% possession, one shot and one on target. Across four opponent reports, all used CLEAR for 69–96% of commands; treat that as a report label, not proof of intent. Amber Arcs and FantasyFootball command totals conflict with their award counts, so exclude those two reports’ latency/action figures from conclusions. Amber Arcs 2 was rank37 before the game (62P, 36W/0D/26L, 84:59) and rank37 after (63P, 36W/0D/27L, 85:61). Its report mix was CLEAR 69%, PASS 17%, PRESS 8%, INTERCEPT 6%; 5 shots, 1 on target, 60% possession. Our report is inconsistent (15 total commands vs FWD5 award says 41), so exclude its own latency/action numbers from conclusions.

L02 native V2 failed its predeclared first-call latency gate (all six first-in-session calls exceeded one second); it is not installed, Fitness was not run, and no L02 games were played. Continue the baseline series while collecting comparable opponent reports. Candidate release remains priority once a new exact build passes native screening, fresh Fitness, and verified configuration readback. See `research/v3/ranked-batch-16.json` and latest coach review.


Owner resumed live play while a new MID release is prepared and asked to
prioritize deployment and games on that release as soon as it is ready. Ranked
batch16 now has 2/5 baseline games recorded: Gork ’n’ Mork Boyz 2:0 and Ada
2:1. Ada report: 36–64 possession, 2–1 shots/on-target, 324 vs 58 commands,
845 vs 15 ms team mean; Ada used CLEAR on 54/58 commands (93%). Our per-role
means were 623/926/902/613/891 ms; Ada 2/2/2/2/73 ms. These are match report
averages, not per-invocation deadlines. Leaderboard now rank13, 166 played, 299
points, 98W/5D/63L, goals224:141. No causal claim from this single game.

Research main now contains L02 at exact commit
`53a409b51297781db512b694df0cb627dd14a951`. L02 keeps L01 policy byte-for-byte
and changes only the stdlib HTTP/SSE runtime entrypoint; native gate and Fitness
remain pending. Current lineup is unchanged, formation1-1-2. Finish any live
match before native checks or lineup change. Create an isolated L02 Runtime from
the exact commit; require 224/224 complete valid calls, zero late including all
six first calls, p95<=800ms, then fresh Fitness5/5. Only then replace MID and
prioritize five ranked L02 games. Keep MID15 rollback and all four other slots
and formation unchanged. See the research checkout's `mid_fast_v2/README.ru.md`.

## Latest checkpoint — 2026-10-25, L01 installation attempt

Owner redirected priority from the baseline series to installing L01; ranked
batch16 is stopped after its first recorded game and is not being continued.
An already-started incoming match versus EPAM Spor finished 1:3 on the previous
setup; it is not an L01 trial and no shots, possession, or event timeline were
captured. Portal returned READY TO PLAY afterward. No lineup settings changed.

L01 candidate Runtime was independently read back as READY with the expected
source commit, archive hash, Python 3.13 entry point, and MID player binding.
Native screen produced 224/224 complete valid decisions, but failed the official
1-second deadline: all six first-in-session calls were 2.37–3.42 seconds. Later
calls had p95 127 ms; overall p95 was 145 ms. All six probe sessions were stopped.
Candidate was not assigned to the MID slot; Fitness and ranked L01 games were
not run. The previous MID and other four bindings remain registered. Do not
relax the first-call gate. Sanitized receipt and reason are saved on GitHub main
at `726c826` in the research checkout. Next step is a new cold-start mitigation
experiment with the same gate; do not start more games on the previous setup.

Current allowance last checked at 21% used. At 5% remaining, stop new matches,
finish in-flight work and verify a safe GitHub checkpoint.

## Current checkpoint — 2026-10-25 (after ranked batch 15)

Batch15 complete: five real ranked matches, unchanged baseline FWD1v16 / existing FWD2 fast path / formation 1-1-2. Result 4W/0D/1L, 10:3 goals, 12 points. Fresh Fitness 5/5 passed before series. See `research/v3/ranked-batch-15-analysis.ru.md` and `research/v3/ranked-batch-15.json`. No active match after completion; portal table was inspected. P01 remains rejected at paired screen and was never installed.

Leaderboard before/after: rank15, 156 games, 274 points, 206:136 to rank15, 161 games, 286 points, 216:139. Deltas agree with 4W/1L. At final snapshot #14 Zorja had 288 points, #10 AgentCore Fighters 321, #8 Amber Dragons X 367. Rivals are actively playing, so these are moving gaps, not fixed targets. Next series can continue only after quota and workshop window are refreshed.

Across batch15: 48:17 shots, 10:3 on target, 34% average possession; 10:3 goals. The three wins at 23–30% possession suggest low possession is not automatically harmful, but this small all-HOME sample does not prove it is an advantage. Report latencies 405/647/2219/744/803ms, median744ms; one match-average exceeded 1s. An internal inconsistency in the Invariant FC report shows 16 total commands but FWD5 award says 52; preserve as anomalous and exclude its command total from interpretation. No distance-of-shot/event timelines confirmed. Do not change setup; seek exact traces and event-level evidence.

Codex quota last checked 17% used after batch14. Workshop last observed 4h24m remaining before batch15 began. Recheck both. At <=5% allowance remaining, do not start new matches; finish in-flight and checkpoint safe data, then verify remote.

## Current checkpoint — 2026-10-25T07:02:19.911385+00:00

Quota at batch12 start: 1% used / 99% remaining; after game5: 9% used / 91% remaining. Historical 5% stop below is superseded by changed quota and owner continuation. Latest owner cohort size is TEN real games, overriding older five-game notes. No shutdown or VPN change.

Batch11 complete: 9W/0D/1L, 18:4; leaderboard 134P/78W/4D/52L, 180:116, 238points, rank17. Exact account delta matches these ten games. Analysis and timestamp-quality correction in research/v3/ranked-batch-11-analysis.ru.md. Legacy completion times were unreliable; Git record times are separately labelled.

Batch12 running, 5/10 complete: 3W/0D/2L, 6:4 goals. Next game6 pending; exact current live state is in research/v3/ranked-batch-12.json. Owner scope: this branch plays and collects data; lineup/setup changes only on explicit request. Portal freshly READY TO PLAY, Fitness5/5 PASS; four original M8 Nova2Lite plus fastFWD2 stance/rev9/source931af03, formation112. Unchanged setup. Do not change bindings/models/prompts/formation or probe while a match runs. Check quota between games; stop new starts at <=5%.

Separate research worktree ../agentic-fc-research, branch codex/model-prompt-lab-20261025. It must not mutate AWS/live configuration or launch matches. Research found teamwide report latency includes model-free FWD2; exact layer cause unknown. Next diagnostic is exact-session read-only timestamp correlation while idle.

Current IAB portal tab7 MY TEAM; workshop16, CloudShell17.

## FINAL QUOTA CHECKPOINT — 2026-10-24T21:44:47.767478+00:00

Owner quota guard reached:5% remaining. DO NOT start matches or experiments.
All in-flight games finished, portal READY TO PLAY, no active game observed.
Goal not achieved: final/winning/<=10ms remain unproven. This is quota finalization,
not success or a user-requested pause. Do not consume reserve on repeated status.
Resume substantive work only with changed quota or explicit owner steering.

Selected working setup:4originalM8 + fastFWD2 stance/source931af03/revision9,
formation112. Native34/34/stoppedtrue/Fitness5/5; all5 fresh real sessions verified.
Cohort10:2W3L,6:6goals,22:32shots. Soccer0:2,Singularity0:1,
AgentCore Fighters2:1,Tik&Taka1:2OT,LFC3:0.394exactresponses389stance+5bootstrap,
0modelcalls. Table119P66W3D50L157:110,201points,rank17. No extra incoming games.
Last two cohorts are2W3L each; previous4W1L is not representative proof.

Canonical selected manifest research/v3/final-setup-20261025.json and
FINAL_SETUP.ru.md. Old20261024manifest explicitly historical-superseded.
Recovery includes original5Harness/profilebaseline-m8 then fastFWD2replacement;
newaccount full restore untested. Archive/source hashes verified prior checkpoint.
Public Git excludes credentials/raw states/ARNs/screenshots; private.local retained.
CloudShelltab17 reconnected,input107,cwdnhitl-fast-v2,HEAD931af03.
Portal7 MY TEAM READY,workshop16. Private cohort10bindings/screenshots in
.local/ranked-batch-10; completeaudits onCloudShell, publicsummary exported.

Next genuine improvement after resume: trace own GK/DEF/MID/FWD1 live invocation
and physical effect. Report counters/columns are not a reliable substitute.
Do not introduce a new model or all-role rewrite without this evidence.
No newPractice/Benchmark, no new automation, no shutdown, VPN unchanged.

## Active series10

Revision9 stance/source931af03 verified in first fresh real game:71stance+1bootstrap,
72responses,0models,CPUmedian.424ms. Soccer L0:2,shots2:9. Second game
Singularity FC currentlyLIVE, do not deploy/probe. Remaining target3 further
games after this match. Quota10%, stop new starts<=5%. Series/bindings under
research/v3/ranked-batch-10.json and private.local/ranked-batch-10.
Prior turn was progress; restoration saved fb732ae.

## Current checkpoint — 2026-10-24T21:16:07.810707+00:00

Cohort09 COMPLETE5/5:2W3L,5:5goals,24:32shots,2scoreless.195points/rank17,
114P64W3D47L151:104. Five matched games explain exact account deltas.
Outlet not promoted. Returned stance via source931af03/revision9; fourM8/112
unchanged. AWS READY exact readback, native34/34, own probe stoppedtrue,
warm105.301ms median/134.873max. Portal Fitness5/5, READY; no active match.
Fresh real-game verification of revision9 stance still required. Do NOT claim
10ms transport or finalist. Current source stance preserves baseline policy.

406 exact own cohort09 responses:401outlet+5bootstrap,66outletMOVE_TO,zero
models,CPUmedians0.408–0.572ms. Public audits/results saved. Report attribution
remains inconsistent, no automatic team-column inversion. No Practice.

Remaining quota11%; <=5% no new starts, finish in-flight and finalize/push.
Goal remains active; hardend02:38:51UTC25Oct/laststart02:28:51. Next useful step:
five real games on restored stance, verify first fresh session, no new candidate
until cohort completes. Existing power/VPN settings unchanged.

Recovery current manifest931af03 verified against archive ef9b7c7... and all9
Git source hashes. Archive .local/fast-path-v2/outlet-candidate.zip contains same
code for both modes; set FWD2_MODE=stance. Baseline older8b31760 preserved in
Git history; original M8 recovery intact. New-account end-to-end still untested.
CloudShelltab17/input50,cwdnhitl-fast-v2,HEAD931af03,pilot-v9/native-v9.json.
Portal7 MY TEAM Fitness5/5; workshop16. Preserve these tabs for continuation.
Private .local/ranked-batch-09/bindings.json/screenshots, raw audits onCloudShell.

## Current continuation — 24 Oct, 21:05 UTC

Cohort09 revision8 outlet/source931af03 remains active. First three real games:
L' Espresso W1:0; Pandavas L0:2; FC Zukko L0:1 (shots0:10). Fourth against
FantasyFootball is in progress. Do not deploy/probe during match. Fifth pending.
Latest quota14% remaining; <=5% stop new starts and finalize recovery/push.
Exact third-session audit:65 responses,15 outlet MOVE_TO,one PASS,zero models,
CPU median0.43134ms/max1.063938ms,source931af03. Portal own row only8 CLEAR
and2–3ms is inconsistent with this audit; attribution unresolved, not a proven
speed win or critical runtime failure. Other4 original M8/formation112 unchanged.
Native34/34 andFitness5/5 already verified. Baseline stance recovery preserved.
Public results research/v3/ranked-batch-09.json; private bindings/screenshots
.local/ranked-batch-09. CloudShelltab17/input50,portal7; preserve both.

## Historical candidate preparation — 24 Oct, 20:45 UTC

Previousgoalturn progress: cohort08completed4W1L/saved9abc3b2.
Now HOMEFWD2outlet implemented/source931af03,pushed.13localtests pass.
AWS revision8modeoutlet READY/native34/34/stoppedtrue. Fitness5/5passed.
Firstrealcohort09matchmakingnowrunning; donotprobe/deploy. CloudShelltab17,input50.
PortalREADY beforeupdate. Do notduplicate orstartmatchuntilnativecomplete/Fitness.
OtherfourM8/112 unchanged. AWSrepoHEAD931af03. Currentpilot receiptpilot-v8.json.
Newmode onlyknownownpossession/HOME/validatedrawframe; boundednonsprinting
passingoutlet, occupiedtargetsrejected. AWAY/restart/unknown/onball baseline.
Baselineartifact/recoverymanifest8b31760 retained; candidatemani under
research/v3/fwd2-outlet/artifact.json. Native/Fitnessverified; exactnewlivebuildnotyetverified.
Next5realgamescohort09 aftergates; noPractice. Rollback931af03mode stance
(commandsbaseline), or exactsource8b31760. Quota19%atturnstart, guard<=5%.

## Active checkpoint — 24 Oct, 20:43 UTC

Cohort08 COMPLETE5/5:4W1L,9:5goals,32:21shots,+12pts. Table109P62W3D44L,
146:99,189pts,rank17. See research/v3/allcash-benchmark/COHORT08.md.
Owner requires FIVE real games/block; no morePractice/Benchmark. Quota20%at20:39,
check betweenmatches; <=5%stopnewstarts,finalizeallrecovery+verifiedpush.
Goalactive, hardend02:38:51UTC25Oct; nonewmanualgamesafter02:28:51.

Currentregistered: fastFWD2revision7/source8b31760,stance, fouroriginalM8,112.
405exactownresponsesconfirm400stance/5malformedbootstrap,0probe-wide/0models/
0geometryfail. Noactiveprobe/match atlastfinal; check portalREADY beforechanges.
Native32/32 andFitness5; drilloldsessionmodewasstale, realgamesverifynewmode.
PhysicalHOMEFWD2movementsupportedtwointervals frompriorcompleteddiagnostic.
Noautomaticcolumninversion; reportattributionstillunresolved. Fullnative~105ms,
not10ms. Energy varies; Apocalypseend0butwon. Currentcandidate remainsfallback.

Nextonecandidate(notimplemented): HOMEFWD2nonsprintingoffballoutletposition,
onlyknownOURSteampossession+validatedframe, keepbaselineAWAY/uncertain/restart.
Otherfourmodels/roles/112 andonballguards unchanged. Native/Fitnessthen5realgames,
neverPractice. Rejectunsafecommand/geometryfailure; rollbackrevision7stance.
Don'tspendwholewindowonlatencyarchaeology; nonewfoundationmodelchosenblindly.

CloudShelltab17reconnected,input123,cwdnhitl-fast-v2,HEADc880ac2; deployed8b31760.
Privatepilot-v7andcohort08rawtracesunder.local/ranked-batch-08; sanitizedaudits
exportedlocally. Portalbindings.local/ranked-batch-08/bindings.json; screenshots
.local/fwd2-control-20261024/. Preserve tabs7/17/16. RecoveryZIP2859a84...all9sources
match8b31760; manifestcurrent, freshWorkshopcreationuntested. Existingpower/VPN/
shutdownunchanged. Nextturncontinuegoal; do notmarkcompletefrompositivecohort.

## Active checkpoint — 24 Oct, 20:14 UTC

Owner now requires **5 real ranked matches per block**, no more Benchmark/Practice.
Owner added quota guard: check Codex remaining between matches; at <=5% do not
start new games. Finish in-flight game, save all safe configs/results/recovery to
GitHub, verify remote commit, and finalize checkpoint. At20:14UTC 25% remained.
Start finalization earlier if needed; reserve enough quota for verified recovery.
Current cohort08 first game KERON FC HOME preparing; no probes/deployments.
Registered FWD2 revision7/source8b31760 **stance**, other four M8 and112 unchanged.
Probe-wide revision6 Practice completed3:0,6:3shots,30%possession; excluded.
Revision7 native32/32,warmmedian105.039ms,ownprobe stopped. PortalFitness5/5,
but drill logs stillprobe-wide from reused/old session: fresh game mode needs
confirmation. Update20:15UTC: genuine game first17 responses confirm16 stance
and1 malformed bootstrap/no mode, zero probe-wide. Runtime readback/native verify stance. Do not stop game sessions.
Current portal binding private .local/ranked-batch-08/bindings.json.
Private control window exported .local/fwd2-control-20261024/window-trace.json;
79decisions,7diagnosticMOVE,0models,CPUmedian.558ms. Physical review pending.
AWS tab17 input50,cwdnhitl-fast-v2,HEADc880ac2. Receiptpilot-v7.json.
Goal/end/power unchanged. After5games analyzeonecandidate,saveGitHub/recovery.

## Active checkpoint — 24 Oct, 19:56 UTC

Goal active, hard end02:38:51UTC25Oct; no manual starts after02:28:51.
Registered: fastFWD2revision5/source8747a88 plus four originalM8,formation112.
Do not mistake historical M8-restored text below for current registration.
Cohort07 complete1W1D1L:Octopus3:1,Octopus0:0OT,AmberGeysers2 0:1OT.
Table104P58W3D43L,177pts,137:94,rank17. Six current-setup games4W1D1L,13:2.
[Latest analysis](research/v3/allcash-benchmark/REPLICATION_AND_LATENCY.md).

No next game/probe running at lastREADY observation. Native GKInvokeHarness
2.39s/1.04s; model897/644ms. Fast full warm101.6/109.2/104.7ms, body<0.3ms.
GKInvokeAgentRuntime(HarnessARN,prompt-envelope) failedResourceNotFound; game
server route unknown. Report role/team attribution unresolved, no model change.
Successful own probes stoppedHTTP200. Compatibility probe confirmed absent.
CloudShell reconnected, tab17 input107, cwd/home/cloudshell-user, repository at
nhitl-fast-v2/source8747a88. Audits/helpers private underits .local/allcash-benchmark.

Next: preserve positive geometry correction and ownership safety; one bounded
physical FWD2 support/action check before choosing a tactical change for next3.
Two scoreless games make attack quality relevant, but no long-shot-distance proof.
Don't spend the whole remaining window on latency archaeology. Current candidate
provisional; exact originalFWD2rollback kept. No all-five wholesale replacement.
Portable fast builder/recovery added; rebuilt9sources match8747a88,9tests pass.
Fresh-workshop creation not tested. Existingcaffeinate57249 still live with both
assertions; no new timer, shutdown, VPN or IAM changes. Preserve tabs7/17/16.

## Interim checkpoint — 24 Oct, 19:36 UTC

Cohort07 is2/3complete on the same registered revision5fastFWD2+fourM8,112.
Two manualHOME games againstOctopus:win3:1(shots8:2),draw0:0afterovertime.
Draw report has noSTATS section; shots/possession remain null. No setup changes.
Third ranked game remains. Owner reinforced periodicGitHub saves andlatency goal.
After the third game:read-only role/call-route attribution check andonecohortreview.
No new model/prompt/deployment until the block finishes. See ranked-batch-07.json.

## Active checkpoint — 24 Oct, 19:23 UTC

Goal remains active, hard end02:38:51UTC25Oct; no manual starts after02:28:51.
Current registered setup is **four original M8 roles + fast FWD2 revision5**,
source8747a88,formation1-1-2. This supersedes the restored-M8 notes below.
Fitness5/5, native28/28, Practice4:0. Ranked cohort06 completed3/3: three wins,
10:0goals,29:4shots,+9points. Fresh table101P57W2D42L,173pts,134:92,rank16.
AllCash1st,256P581pts. See [result](research/v3/allcash-benchmark/RESULT.md).

Retain provisionally for cohort07, three games unchanged. No new model/prompt
or formation change. Confirm READY/current binding and fresh start snapshot.
Audit241rankedresponses:0UNKNOWN_GEOMETRY,CPUmedian0.409–0.552ms,zeroLLMcalls.
FullAWSnative~103ms; report attribution unresolved,10msgoal unachieved.
All3HOME/nonleaders; historicalM8also beatForza2:0, so no causal win claim.
Exact rollback remains originalFWD2v14 in `.local/live-test-20261024/`.
Private current evidence `.local/allcash-benchmark-20261024/`; CloudShell
`nhitl-fast-v2` at8747a88, pilot receipt `.local/fast-path-v2/pilot-v5.json`.
Do not stop ranked sessions or probe/deploy during a game. Preserve tabs7/17/16.

## Active goal resumed — 24 Oct, 18:44 UTC

Owner renewed autonomous6–8h objective with **three-game blocks**, AllCash United
as benchmark. Active goal created18:38:51UTC; hard end02:38:51UTC25Oct, stop
manual starts02:28:51UTC. This supersedes historical stop/five-game instructions
below. No shutdown/VPN change/new heartbeat. Existing live caffeinate assertions
verified18:42UTC, no new timer. Previous turn was progress, not goal completion.
Read coach-v1.0 and current evidence before each block. M8 still registered,
READY,rank15/164pts/98P; AllCashrank1/563pts/248P. Benchmark and hypotheses in
research/v3/allcash-benchmark/. Investigate latency attribution and moving-GK
reference before one isolated correction, native/Fitness/Practice then3livegames.
Never change active games, preserve private evidence and exact M8 rollback.

## Live latency experiment closed — 24 Oct, 18:33 UTC

[Result](research/v3/compact-role-r2/RESULT.md), [outcome](research/v3/compact-role-r2/outcome.json).
Original M8 is restored:five original Harness,112,Nova2Lite x4,Haiku FWD2.
Fresh restored Fitness5/5 at18:29UTC; final API readback all five config/prompt
settings unchanged. Exact versions13/19/15/16/14. Fast FWD2 unregistered, own
Fitness session stopped. Its unused AWS Runtime/code artifact remain available;
no ranked/game sessions were stopped or deleted. No10ms end-to-end claim.

Batch05 ended2/5 on critical11.66s all-role/zero-command report. Two manual losses
plus incoming baseline Octopus loss and pilot AllCash loss reconcile94→98games,
164→164points,123:84→124:92. Latest saved table18:29:25UTC:15th,164pts,
98P54W2D42L. Practice1:0 is excluded from these real results.

Five compact role prompt candidates updated and rejected:36actual Converse
calls, Nova0/9,Haiku0/9,Sonnet3/9,Micro1/9; none<=10ms. None installed.
Fast deterministic FWD2 (no per-tick model) latest deployed b99bf77 passed22/22
native andFitness5 after two documented startup failures, won Benchmark1:0/6:5
shots, lost incoming AWAY AllCash0:2/5:9 during Practice. Full AWS warm median
105ms; own compute<1ms in both games. Practice62responses59CLEAR/3STANCE;
AllCash75responses35CLEAR/38STANCE/2PASS. Not adopted. Report attribution and
shared latency spike unresolved; do not claim winner, wrong-player routing,
LLM training or a completed five-game cohort. No automatic next experiment.

One proposed next correction:verify pinned pitch reference versus moving GK
before more live tests. It is not implemented. Preserve ownership safety.
Private evidence/bindings:`.local/live-test-20261024/`. AWS private receipts:
CloudShell `/home/cloudshell-user/nhitl-fast-v2/.local/fast-path-v2/`.
Source/pilot code and negative results retained in Git. AWS login refreshed via
existing Workshop, no new terms/IAM. No heartbeat, power timer or old8h loop.

## Role-package experiment rejected — 24 Oct, 17:29 UTC

The owner-authorized five-role prompt package was prepared and tested with real
Bedrock calls. All three revisions failed:0/21,3/26,2/26. See
[result](research/v3/role-package-r1/RESULT.md). **Do not deploy these prompts.**
No candidate resource/registration/Fitness/ranked match was started. Original
M8 remains the operational setup; models, history, formation and IAM unchanged.
The five-game cohort never began because its prerequisite failed. No heartbeat,
power timer or historical autonomous loop was resumed.

The owner emphasized latency. Context probes found stale passes and roughly
3x input growth, but no causal diagnosis of live losses. Fast opponent
ForzaMilan13 (2–3ms) lost0:2, shots0:9; own report818ms/369commands versus
opponent2ms/13commands. Do not treat fast/success100% counters as useful execution.
Latest observed table15th/161points/93P53W2D38L/121:84. Four background games
since the saved89P checkpoint reconcile exactly; none used the candidate.
The proposed next step is code-checked compact model choices with end-to-end
timing, not another unchecked expansion of all five prompts. It is not yet
implemented or tested as a winning setup. No automatic follow-on experiment.

## Superseded start of bounded role-package experiment

The owner explicitly requested all five role improvements together as one
experiment, then emphasized coordination, understanding constraints and avoiding
low-quality shots/turnovers. This new instruction authorizes the bounded
[role-package-r1 protocol](research/v3/role-package-r1/README.md). Five prompts
are the bundle; models and formation1-1-2 remain M8. The prior formation121-only
proposal is deferred. No historical eight-hour loop, heartbeat or power extension.

At the start: prepared locally; live candidate gates were not yet completed. Original M8 remains
registered. Require actual model21/21, isolated resource readback, no active game,
candidate registration and Fitness5/5 before one stable five-game cohort.
Failure or inconclusive evidence returns to original M8. Do not report the
candidate as working or stronger before obtaining evidence. Keep new results
separate from the frozen80-report decision audit below.

Fresh portal read this turn: original five,1-1-2,READY TO PLAY. Latest observed
leaderboard is15th/158points/91P52W2D37L/119:81; two background games since the
15:39snapshot (Amber Crests2 win0:1 AWAY; Zorja loss0:2 AWAY). These are not
candidate results. Exact read timestamps are not yet saved with this note.

## Bounded offline mission — 24 Oct, 16:54 UTC

The owner requested one win-oriented research/engineering iteration, explicitly
excluding new live matchmaking, AWS deployment and heartbeat changes. Read the
[tournament decision](research/v3/TOURNAMENT_DECISION_20261024.md) and its frozen
evidence/evaluation assets. A remains the saved M8 fallback; B (only formation
1-2-1, the same five original Harness) is the sole prepared next experiment.
Its five-game protocol requires separate explicit authorisation and a new bounded
window. Do not resume batch04, the historical eight-hour loop or the heartbeat.

The latest live verification remains 15:39 UTC below, not a new portal read.
The mission changes analysis/evaluation and corrects FWD1 export-version prose;
no agent prompt, model, runtime code, AWS resource or power schedule changed.
Offline adversarial audit found an unhandled players=null case in the unused R1;
this is not a demonstrated cause of M8 losses. No autonomous follow-on research.

## FINAL OWNER DIRECTIVE — 24 Oct, 15:31 UTC

The owner ended exploratory work and requested finalisation using existing
evidence. This supersedes the five-game loop and original eight-hour window
below. **Do not resume experiments, probes, deployments or manual matchmaking
without a new human instruction.** The existing heartbeat is PAUSED, verified
by tool response and saved configuration. No shutdown or Chrome cleanup.

Final setup: **M8, original five Harness, formation 1-1-2**. GK/DEF/MID/FWD1
use Nova 2 Lite; FWD2 uses Haiku 4.5. Original saved prompts, no Memory or tools.
Current role versions: 13/19/15/16/14. FWD1 v16 has the same saved prompt/config
as the original baseline. The bundle records sourceVersion15 and baseline-m8
disables its optional memory association; pre-memory FWD1 was v14. Revision
numbers are resource-local history, not portable configuration identity.
Formation persisted after reload and fresh Fitness passed all five at15:39UTC.
Experimental FWD1 and GK runtimes are unregistered.

The already-running live80 finished1:0 against Mobile United FC, shots6:6.
Formation121 trial ended at **1/5 by owner instruction**, not a complete cohort.
Final leaderboard snapshot15:39UTC: **14th,155points,89P51W2D36L,118:79,+39**.
M8 stable controls:10games5W1D4L,16points. FWD1v14 candidate:5games1W4L,
3points; not adopted. Opponents/sides were uncontrolled; M8 is a supported
final choice, not a proven global optimum or tournament-winning guarantee.

Start with [final setup](research/v3/FINAL_SETUP.ru.md) and
[machine-readable manifest](research/v3/final-setup-20261024.json).
Restore explicitly with `--profile baseline-m8`; full fresh-account restore
remains unverified. Preserve private receipts under ignored `.local/`.
Git branch `codex/football-experiments-20261023`, draft PR5; do not auto-merge.
The original bounded awake timer may expire normally; display sleep allowed.

## Historical instructions and checkpoints — superseded where conflicting

## P0 OWNER DIRECTIVE — PLAY FIVE LIVE MATCHES, THEN ANALYZE (24 Oct 2026)

**Read first on resume. This is the owner's newer priority and overrides the
older one-game-at-a-time experiment instructions in "Next useful work" and
timestamped notes below.** See [GitHub Issue #6](https://github.com/dkharlanau/agentic-fc/issues/6).
Do not assume an Issue/PR comment automatically reached the active Codex run.

**Execution loop during the EXISTING authorized session:**

1. **Finish any already running live match first** without altering agents,
   configuration or game sessions. Respect portal rules and do not run parallel
   matchmaking. Determine which portal mode actually counts toward the ranking.
2. Capture an actual **fresh timestamped leaderboard** (rank, points, W/D/L,
   games played), recent ranked-match history and the exact five-role setup.
   Save raw screenshots/private identifiers only in ignored `.local/`.
3. Use a **single verified stable lineup** — original M8 (five original M7
   Harness roles, formation 1-1-2, Fitness 5/5), unless an objectively better
   lineup is *already* verified. **Play FIVE completed real leaderboard-eligible
   matches against other teams consecutively with exactly that lineup.**
   Do not change prompts/models/GK/FWD1/formation/Runtime within the block.
4. **Between matches:** only note opponent, HOME/AWAY, outcome, score and
   available primary stats; start the next eligible match promptly. **No
   deep postmortem, synthetic tactical rounds, new prompt, redeploy, Practice
   or model benchmark after each ordinary win or defeat.**
5. **After all five completed matches:** refresh the leaderboard screenshot.
   Analyze the entire 5-match block ONCE: change in rank/points, W/D/L,
   aggregate goals and shots, recurring weaknesses, and reliability. Decide
   whether to retain setup or test **at most one measured tactical change**
   for the NEXT block, keeping the previous stable setup as rollback.
6. Repeat another five-match block (aim for 10–15 additional ranked games
   overall) if scheduling, access and event constraints permit. When the
   authorized match-start cutoff arrives, stop starting new matches; summarize
   any partial block honestly. Never extend the authorized window on your own.

**Only interrupt a five-game block for a critical error or rule issue:**
Fitness/NO_PARSE/JSON failure, wrong team/player mapping, unsafe commands,
broken live portal/resources or similar serious reliability failure. A
normal match loss is **not** a reason to interrupt the cohort.

**Deliverable:** short sanitized per-batch report under `research/v3/` showing
time, setup, five results, **fresh before/after leaderboard** and changes in
rank/points; link it from Issue #6 / PR #5. Keep Practice and diagnostics
separate from live/ranked matches. Do not fabricate screenshots, metrics or
game completions. If the portal cannot be accessed, record that blocker.

**Until the first batch is complete, defer optional v13/Practice07,
20-case model rounds and further keeper/forward diagnostics**, except when
needed to repair a critical game failure. User's objective is to gain
tournament points through playing more opponents, not to endlessly tune
between matches.

Same active goal: prepare a fast, reliable tournament team through real matches,
critical self-interview rounds and reproducible Git history. Work autonomously.

## Window and boundaries

User renewed the eight-hour window at2026-10-24T09:14:05Z. End17:14:05Z
(20:14:05Europe/Minsk); stop new manual games17:04:05Z. Save/push final setup,
disable the existing heartbeat at the end. **No shutdown or Chrome cleanup.**
VPN unchanged. Private checkpoint `.local/aws-20261024-sixhours/current-run.json`
has the owned caffeinate PID, assertions, active game and private AWS bindings.
Computer Use for AWS/portal/visible CloudShell; local files/tests/Git allowed.
No local AWS APIs, IAM expansion, SCP bypass, messages, extra chats or subagents.
Check portal before native probes or saved changes; do not alter active games.
Stop only own probe/Fitness sessions, never match sessions. Keep raw states,
account/resource/session bindings and access codes out of public Git.
Branch `codex/football-experiments-20261023`; draft PR5 already attached.

## Current verified checkpoint at14:34UTC

Two stable ranked batches finished: live63..72,10games5W1D4L,12:11goals,
16points. Fresh14:31leaderboard:14th,149points,81P49W2D30L,111:68goals,+43.
Batch01=3W0D2L9points; batch02=2W1D2L7points. All accountchangesreconciled.
One severe live69zero-command/high-latency signal; unchangedFitness5passed,
exactgameDEFlogsabsent, causeunknown. Latergamescommandcountsrecovered.
ReportRESET18inlive70unattributed; do not assume ownphysicalexecution.
Live72draw0:0afterOT hasnoSTATS; shot/possession valuesnull, notzero.

Coach-v1.0read and decisionsC01/C02/C03 inCOACH_REVIEWS.md. NewAGENTS.md
requirescoachreadbefore/afterblocks,briefreview andmaxonechange. Readit.

Currentonlycandidatechange: FWD1R1v14positionbound inportal; freshFitnessRUNNING.
OriginalGK13/DEF19/MID15/FWD2v14 unchanged,112,Nova2LiteFWD1,HaikuFWD2.
R1sourcee11bad6,archive516464b636877353d137f097bdbb83912423ffe74421402acbba7a0c00faaa90,
READY/native9of9genuinechoice/command/cleanup passed; allownprobesstopped.
No coordinateprobe, boundwire, supportposition. GKcandidateUNREGISTERED.
RequireFitness5beforePractice08Benchmark; inspectactualmovement/support,
thenreturntopoints viaanotherstablefivegameblock usingverifiedsetup.
Rejectonwrongrecipient/frame/format/regressingsupport; rollbackoriginalFWD1v16
fromprivatecheckpointandfreshFitness5. NoMicro/GK/formation/observeralongside.
Noactivegameatbinding, recheckportal beforeprobes/savedchanges. Nextlive73,
nextPractice08. PR5descriptionthroughlive67; refreshnearfinal. Olderchronological
notes below arehistorical. Matchcutoff17:04:05Z,end17:14:05Z,noextensions/shutdown.

## Historical snapshot at11:46UTC

Formation1-1-2. FWD1 independent R1v11, Nova2Lite, bound output scope,
optional attack-support stance enabled. Other four original M7 Harness unchanged:
GK13/DEF19/MID15/FWD2 14; FWD2Haiku4.5. Original FWD1v16 rollback preserved.
R1v11 source7a14d1b, archive8554b6aa9189c3bbefe9ed100fd494261a85212777250106b500770e587efb81.
READY readback, native7/7 genuine-choice/cleanup and fresh Fitness5/5 passed.
Own fixed Fitness session was already absent/terminated; do not claim stop200.

Practice04 completedHOME vsBenchmark2:0, shots7:5, possession36%; Unity final
matches primary report. R1 emitted75choices:40STANCE,31CLEAR,3PASS,1INTERCEPT,
zero input rejects; modelp50=406/p95=511/max609ms. Own previousINTERCEPT
snapshot has ownCoachIntercept, opponentCoachMoveTo. This supports own control
for that observation; report command columns still show own-like data under
opponent. STANCE absent from rendered command totals. Do not invert team IDs.
Primary outcomes match Unity; AI Overview is not causal evidence.

A separate GK candidate is now READY/native11of11 and registered in GKslot;
fresh portalFitness is running. Read `.local/r1/gk-deploy1.stdout` and private `gk-receipt1.json`
in CloudShell checkout `/home/cloudshell-user/nhitl-r1-source-7ae12c1`.
It uses the same reviewed v11 archive, player0, bound wire scope, Nova2Lite,
separate actor, existing role/bucket only. All11native cases passed and own sessions stopped. Require fresh Fitness5/5
and matched Practice05 against Benchmark.
Keep FWD1v11/four other settings fixed to isolate goalkeeper. If native fails,
inspect without weakening gates; original goalkeeper remains registered.

## Evidence and decisions

-60live reports in `research/v3/matches.json`; nextlive61. Lastlive59AWAY
 Matrix_7 lost0:1(shots3:1); live60AWAYLFC won1:0(shots9:0).
-4Practice reports separate in `practice-matches.json`; nextPractice05.
 Benchmark: originalM8=3:1/8:6shots; R1v8=1:0/4:10; v9=3:0/6:4; v11=2:0/7:5.
 Archetype stable, seed not fixed. No candidate superiority established.
-Original five M7 Harness on112(M8) remain working reference:12recorded
 games10W/1D/1L,20:4goals,97:24shots, plus later original-FWD1 control7:0.
 Different opponents/sides confound strength estimates; preserve rollback.
-Model round: Nova andHaiku each8/8legal/target-index synthetic choices;
 reported model medians414.5/796ms. FourHaiku native calls26–33sec wall
 despite~0.8sec model metadata. Cause unresolved; not all 'thinking'.
-CompletedJSONv6 rejected by portalNO_PARSE, even though native5passed.
 v7 exactv5SSE; v8precomputedSSE; v9omits optional wireteamId. v11 addsstance.
 v10native mismatch: old replay expectation and HOMEchoseClear; corrected
 optional selector sentence in v11, native7passed. Do not silently erase failures.
-All current policy/observer/GK offline checks39passed. SDK offline HTTP smoke
 verifies decision-before-response and byte-identical valid SSE; no AWS calls.
-Standalone `runtime_v1/tactics.py` observer remains EXCLUDED from deployment.
 Private adaptive drafts must not be included accidentally. Integrate later as
 an isolated candidate only after field evaluation, not alongside formation/model.
-GK code permits safe distribution and documented-frame recovery only; no
 PRESS/SHOOT/ordinaryPASS/RESET, no guessed world-coordinate MOVE. Native11of11 passed; fresh Fitnessrunning.
-Shot analysis/notebook refreshed throughlive60:59complete reports,420shots,
79SOT/79goals. Distances unknown, SOT=goals throughout; no verified wide-miss
rate, long-shot accuracy or goalkeeper save percentage. Practice excluded.

## Next useful work

1.Finish GK creation/native11, then isolated BenchmarkPractice05 if valid.
2.Repeat promising comparison; test high-press and compact-counter Practice
 presets. Use saved originalM8 controls. Do not accept one winning game as proof.
3.Compare112/121 holding actual bindings/models fixed. Test energy and central
 cover; one nearby eligible outfield presser, keeper stays home, avoid corner traps.
4.If justified, integrate bounded observer: three advancing states over4seconds,
12sec dwell; observed positional shape, not hidden declared formation. Keep a
 single short model call and strict action validation. Preserve source/build.
5.Return to live matches between batches; audit actual build, not READY alone.
6.Update portable final recovery/config, scouting, evidence, README and PR5
 description before deadline. Recovery profiles baseline-m7/baseline-m8 exist;
 `restore.py` defaults m7 for compatibility, choose baseline-m8 explicitly.

Raw evidence is private under `.local/aws-20261024-sixhours` locally and
`.local/r1` in CloudShell. Public status: `runtime-r1.json`, `run-20261024-sixhours.json`,
`adaptive-plan.ru.md`. Latest UI/private checkpoint outranks any older snapshot.
Keep meaningful commentary at least every60seconds; do not spend minutes on
internal analysis between actions. Never claim a top-team/learning effect that
has not been measured.

Latest11:56UTC: GKnative11/Fitness5passed; Practice05draw0:0 afterextraTime
239.114sec, primarySTATSabsent, Unityfinalhasnoshottable. Storeallshot/possession
valuesnull, notzero. GK118genuineCLEARchoices,p50=415/p95=597,max1578ms;
FWD119choices46CLEAR/64STANCE/7PASS/2INTERCEPT,p50=408/p95=508,max650.
No inputrejects on either. No keeper improvement established. Both currently
registered; threeotherM7Harness unchanged. No activegame. NextPractice06.
v12local opt-in --fwd-coordinate-probe world-target offers onlyFWD3 smallraw
MOVE_TO(4*attackSign,1.5,noSprint) forgameTime8..28, thenoldpolicy. Purpose:
resolve outgoingmovementunits andphysicalrecipient usingrawposition/lastAction.
No converter installed.40offlinechecks+SDKsmokepass. Archive96c2a99999154556b1a12853c6988f9607aaa3e3e527b590bb574f21fe2efc01.
Commit/push,Cloudbuild,updateR1receipt11->12 withbound+attack+world-target,
native9cases thenfreshFitness5beforePractice06. GKremainsv1. Diagnostic
outcomesmustnotcountasstrength. Exactv11/GKrebuildprofilesin runtime_v1/profiles.json.

Latest12:14UTC: live61AWAYGoalpostShifters lost1:2afterOT209.17sec,13:10shots,
44%possession; Unityprimarymatchesreport. GK123CLEAR,p50=416/p95=637;
FWD123choices50CLEAR/68STANCE/4PASS/1INTERCEPT,p50=414/p95=561; bothsource7a14,
0rejects. No provenkeeper/attackimprovement. Live62next.
R1v12updatedREADY sourcee52447c/native9of9passed/allownstopped. Oldownfixed
Fitnesssessionalreadyabsent. FreshFitnessrunning; thenPractice06coordinate
diagnostic, GKremainsR2v1. No activegame now. Nativeelapsed4049,4009,3985,4076,
3489,4114,3504,3594,3648ms. MicrocandidateofficialConverse/us-east-1documented;
runneropt-in --models micro prepared, NOTrun/installed. DefaultNova/Haiku
preserved; stoponserviceaccessdenial, noIAMchanges. ModelroundsafterPractice06
inidlewindowonly. Publiceditslive61/runtime status/benchrunner needpush.

Latest12:27UTC: Practice06completed0:1,shots1:5,pos52%; diagnosticexcluded
fromstrength. v12build e524verified64choices27CLEAR/24STANCE/10MOVE/1PASS/2INTER,
0reject,p50=418/p95=560/max1001. OwnHOME3CoachMoveTo at11.72afterfirstMOVE9.7;
subsequentpositionsapproachraw4,1.5withinabout0.53, thendrift/retreatafterwindow.
Ballcontact/dribblingconfoundsthis; do NOTsayphysicalteamsareinverted.
v13localaddsquiet --fwd-coordinate-probe own-wide target(-2*sign,2.8),
same8..28window/model/boundscope.40checks+SDKsmokepass;archive
de7dddef3fa44bfa824849d684c0a1ec3d7dc527bd23d31dcfc356467252e2e0.
NEXT restore BOTHoriginalGK13 andFWD1v16portalARNs whileidle, freshFitness5
soincominggamesuseworkingM8whilepreparing. ThenidleMicro8nativeoverrides
(originalFWD1Harness) withlatestbenchrunner; stoponAccessDenied,noaccesschanges.
Commit/pushv13,Cloudbuild/updateunusedR1receipt12->13 withbound+attack+own-wide,
native9thenbindonlyFWD1beforeFitness/Practice07; GKoriginalforquietercontrol.
AfterdiagnosticrestoreM8betweenexperiments. Bewareincominggamescanstartwithout
consent; checkUIbeforesavedchanges/nativecalls. Currentphaseprivatecheckpoint.

Latest12:35UTC: FullM8(originalfiveHarness,112) restored andfreshFitness5passed.
R1/GK bothUNREGISTERED. Micro8nativeindexchoices onoriginalFWDHarness alllegal/
target, allsessionsstopped, reportedmodelmedian312.5ms vsoldNova414.5/Haiku796.
Publicsafe report tactical-micro-round1.json exported; NOTinstalled in team.
CRITICAL evalreview: constantindex0 also passes8/8originalscenarios; annotate
oldreports, do not claimmodelqualityrankingfromthis. New --option-permutations3
keepssameactions/rotatesindex;20cases/model, constant0baseline12/20. Nova+Micro
40callplan prepared butNEVERrun duringgame; no saves/IAM.
R1v13unusedREADY(source88eb47f,quietown-wide,boundscope,Nova2Lite);native9
running. NextbindonlyFWD1forPractice07afterpass/Fitness; GKoriginalstays.
Observe early8..28seconddiagnostic promptly viaScreenshots+allrawsame-IDaudit.
AfterPractice07restoreM8betweenexperiments. Nativebenchnewsource editsneedpush.

Latest12:39UTC: v13READY/native9of9passed/allownstopped;UNREGISTERED. Binding
deferred because incominglive62AWAYClaudeVanDam began onoriginalfiveM8,112.
PrivatecheckpointhasgameID; do not mutatebindings/runtime duringthisgame.
R1/GK remainunregistered. M8currentlyleading0:2fromcommentary(notfinal).
Afterreport, bindonlyFWD1v13→freshFitness5→Practice07quietunitdiagnostic.
ThenrestoreM8. New20case/modelcyclicbenchmarkNova+Micro40callsNOTRUN;
constant0baseline12/20. Microoriginal8casesalllegal312.5medianmodelms but
constant0baseline8/8; donotclaimdiscriminatingquality. Latestpubliceditsneedpush.

Latest13:18UTC: Practice07v13finished2:0,4:4shots,pos36%,diagnosticexcluded.
OwnHOMEFWD3control/rawMOVEunits VERIFIED: two consecutiveCoachMoveTo intervals
10.44->12.46->14.48 align withrawtarget(-2,2.8),cosines.9999994/.999999999998,
versusnormalizedalternative.8394/.3902. OwnblueFWD4wideat23screenshot. No team
inversion; reportMOVE10underopponentis attribution-unreliable. Goalposts
remainkeeperproxy, AWAYphysicalnotyetchecked. M8restored again/Fitness5passed.
Leaguebefore/afterPractice07unchanged71P44W1D26L,99:57goals,133points,rank13.
Current live63next,Practice08next. Micro/Nova cyclic20eachcompleted alllegal/
alltarget/all40sessionsstopped; medians259/393.5ms, constant0baseline12/20.
Public tactical-model-orders2.json safeprojection,sourceD0c328c. MicroNOTinstalled.
v14POSITION support localready: canonicalrole-targetMOVE whenknownoffball,
noSprint, distance>4canonical; existingnearpress/onballguards preserved. Inverse
rawtransform onlyvalidatedkeeperframe; unresolvedreleases. WorldKickoffnow
movement-guarded; native9 includesrawposition/restart HOME/AWAY.43checks+SDK
smoke passed. Package516464b636877353d137f097bdbb83912423ffe74421402acbba7a0c00faaa90.
Commit/pushall,Cloudpull/build,updateunusedR1receipt13->14 withbound,
--fwd-support-mode position,NOcoordinateprobe, Nova2Lite. Require native9 then
bindonlyFWD1/Fitness5/Practice08sameBenchmark. GKandotherrolesoriginalM7.
Do not mixMicro atsame time; later model-onlytrial using samearchive after
positionfieldtest. M8workingreference remainsmain. Publicshotsanalysisstill
throughlive60; update nearfinal. PR5description/recoveryprofiles needfinalreview.

Latest14:03UTC: Batch01finished3W0D2L,9points; coach-v1.0read/reviewed in
COACH_REVIEWS.md. v14 rebuiltidentical516464... and updatedunusedR1READY,
sourcee11bad6, supportposition,bound,Nova2Lite,rawdiagnosticoff. Native9of9
command/model/cleanup passed, allownsessionsstopped. StillUNREGISTERED,
noFitness/Practiceyet. Beforebinding, incominglive68AWAYFCRAMstarted on
originalfiveM8. Therefore defercandidatefieldtest and complete rankedbatch02
withsameM8unchanged. Fresh14:03leaderboard14th,142points,76P47W1D28L,
107:63goals. Savefivegamesthenoneanalysis. Nextmanualreportlive69 afterlive68;
nextPractice08 afterbatch02. No activegame mutation/probe. PR5description
refreshed throughlive67; updateagainnearfinal. Latestprivatecheckpointwins.

Latest14:52UTC: Practice08v14won3:0,5:4shots,27%possession. Correctownsession
auditusesPORTALRECORDUUID,notUnityviewerquerymatchId:79genuinechoices,0rejects,
45CLEAR/29MOVE/3PASS/2INTERCEPT,modelp50=464/p95=882/max925ms. All29MOVE
nonSprint/rawframe; ownCoachMoveTo19afterMOVE. Energymedian.922,end.950,
min.103; nomatchedbaselinecurve,notprovenbetter. EmptyfirstlookupwaswrongID,
notmissingdecisions. Correctedlive69DEFportalUUIDlookupstill0events.
Incominglive73AWAYLFC0:1,5:4shots,52%possession, overlappedalreadyrunning
Practice08. Saveoutsideplannedcohorts;68genuine/0rejects/47MOVE,p95=883ms.
Fresh14:50LB14th,149points,82P49W2D31L,111:69goals,+42.
Rankedbatch03NOWRUNNINGsamev14onlyFWD1candidate,fourotheroriginal,112,Nova2Lite.
Firstlive74incomingAWAYAgenticArsenalcurrentlyactive; allnative/Fitness/Practice
gatescompletebeforethisgame. No probes/saves/model/formationchangesuntilfive
completedgamesexceptcriticalfailure. Nextreportlive75afterlive74; nextPractice09.
COACHv1.0readandreviewedbeforeblock. OriginalFWD1v16exactrollbackprivate.

## 2026-10-25 — ranked batch18 underway

Batch18 completed five real ranked games on the unchanged baseline and 1-1-2:
Feyenoord 0:2, Hallucination FC2 1:2, FC Zukko 2:0, Human Override Disab 1:0,
FC RAM 0:2. Standings: rank12, 179 played, 327 points, 107W/6D/66L, goals
243:147; batch17 closed at 174/318, 104W/6D/64L, 237:143. Batch record 3W/2L,
6:4 goals, +9 points. Reports and opponent profiles are in
`research/v3/ranked-batch-18.json` and `COACH_REVIEWS.md`. All five opponents
logged CLEAR as their most frequent action, 79-90%, observation only. Own
latencies: 73/75/1590/75ms for four coherent reports; FC Zukko's own 2ms report
is inconsistent and excluded. Both losses had zero shots on target; FC RAM
match had 11 SHOOT labels but no target, while Human Override Disab match had
no SHOOT label despite four shots. The 1590ms report and action/shot mismatch
are leads for investigation, not proven causes. <=10ms remains unmet. No
lineup/model/prompt changes or L02 trial. At this checkpoint Codex usage showed
24% used; no need to stop for quota.
## 2026-10-25 — ranked batch19 started

Batch18 is complete and pushed at `2983e00`. A new five-game real-ranked series
is staged in `research/v3/ranked-batch-19.json`; baseline unchanged, 1-1-2,
pre-table rank12, 179 played, 327 points, 107W/6D/66L, goals243:147. Codex
usage last read 24% used. No active game at this checkpoint. Continue one game
at a time, capture reports/opponent details, and analyze only after 5/5. No
practice, benchmarks, candidate install, or configuration changes.

Batch19 game1 is complete: No Human in the Loop beat FootballCore 1:0, with
2434ms report latency, 36% possession, 10:2 shots and 1:0 on target.
FootballCore logged 21/22 CLEAR (95%) and 18ms average. Our post-game row was
#12, 180 played, 330 points, 108W/6D/66L, goals244:147. These details are in
`research/v3/ranked-batch-19.json`; the 2.4s team latency is unexplained, not
attributed to model, service, or network.

Batch19 game2 is ERTT 0:1, a win: 53% possession, 4:6 shots, 1:0 on target;
our report mean 1172ms, 169/185 commands PRESS (91%); ERTT had CLEAR27/30
(90%) and 19ms mean. The GK scored at 2'. Post-game leaderboard #10, 181
played, 333 points, 109W/6D/66L, goals245:147. Batch19 is 2/5. Two consecutive
reports show own mean latency >1s (2434,1172ms); cause remains unknown. Details
are in `research/v3/ranked-batch-19.json`; no configuration changed.

Batch19 game3 is Lighting Cloud 0:2, a win: 36% possession but 11:2 shots and
2:0 on target. Our report showed 1905ms mean, with DEF 5338ms, while Lighting
Cloud had 17ms and CLEAR17/19 (89%). Standings after match: #10, 182 played,
336 points, 110W/6D/66L, goals247:147. This is the third consecutive report
above 1s own latency; root cause still unknown. Batch19 is 3/5; continue without
configuration changes. See `research/v3/ranked-batch-19.json`.

Batch19 game4: Points Donors 0:2, win; 46% possession, 3:8 shots, 2:0 on
target. Our 332-command report showed 456ms, led by INTERCEPT244 and SHOOT27;
Points Donors had CLEAR37/40 (93%) and 17ms. Leaderboard #10, 183 played, 339
points, 111W/6D/66L, goals249:147. Batch19 is 4/5. Keep setup unchanged through
the final game; full report is in `research/v3/ranked-batch-19.json`.

Batch19 is now complete 5/5 on unchanged baseline: FootballCore 1:0, ERTT 1:0,
Lighting Cloud 2:0, Points Donors 2:0, Tik&Taka 2:1 sudden death. Series 5W,
8:1 goals, +15 points. Final standings #10, 184 played, 342 points,
112W/6D/66L, goals251:148; start #12/179/327/107W/6D/66L/243:147. Batch
analytics and opponent reports are in `research/v3/ranked-batch-19.json` and
`COACH_REVIEWS.md`. Own reported latency median1172ms, mean1409.2, range
456-2434ms; four of five exceeded one second. Team CLEAR-heavy opponents were
5/5 (80-95%). We had 33:22 shots, 8:1 on target, despite 41.6% mean possession.
The <=10ms target remains unmet; no setup changed. Codex usage was read after
batch19 and showed 24% used. No model/prompt/formation changes or L02 install.

Batch20 complete 5/5 on the unchanged baseline and 1-1-2: Tajfun Komary 1-0,
Amber Geysers 2 2-1 after sudden death, Le Masia 1-0, Mobile United FC 1-0
after sudden death, Feyenoord 1-2. Record 4W/0D/1L, 6:3 goals, +12 points.
Leaderboard moved #10/184/342 points/112W/6D/66L/goals251:148 to #9/189/354/
116W/6D/67L/goals257:151. Full sanitized match and opponent records, snapshots,
limitations and cohort analysis are in `research/v3/ranked-batch-20.json` and
`COACH_REVIEWS.md`.

Opponents' CLEAR action was the largest category in all five reports: pooled
215/250 commands (86%). Live commentary called several teams high-press or
patient buildup, though reported PRESS actions were typically 0-3; commentary
is not ground truth about policy. Le Masia's observed row was #25 before/after
adjacent snapshots; Mobile United FC #47 before and after our match; Feyenoord
#4 before and after with row movement consistent with its win. Tajfun and Amber
Geysers 2 were not in the loaded top48. These are timestamp-near snapshots with
possible concurrent match movement.

Own reported mean latencies were 15941/847/807/668/82ms (median807, mean3669);
all exceeded the <=10ms target, four of five were below 1s. Tajfun's report is
inconsistent (zero team commands but 15941ms mean and 11-19s roles), cause
unknown. Feyenoord was 82ms overall; Mobile United FC split GK/DEF 2ms and
MID/FWD ~1s. Opponent means were 15-25ms (median17). All report success values
were 100%; no independent timeout audit was available. Codex allowance last
checked after game3 at 24% used; check again before another cohort. No setup
changes were made; do not infer tactical causality from this five-game sample.
