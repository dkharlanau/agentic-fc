# Agentic FC continuation

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
