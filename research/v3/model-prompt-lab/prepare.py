#!/usr/bin/env python3
"""Prepare reviewable local candidate files and reports. No deployment code."""
import difflib
import json
from pathlib import Path
import lab

HERE = Path(__file__).resolve().parent


def patch_for(path, before, after, context=3):
    lines=difflib.unified_diff(before.splitlines(True),after.splitlines(True),
                              fromfile='a/'+path,tofile='b/'+path,n=context)
    # Git accepts empty context lines without a space prefix. This also keeps
    # checked-in patch artifacts clean under git diff --check.
    return ''.join('\n' if line==' \n' else line for line in lines)


def prepare_energy():
    """Independent queued experiment: never stack on P01 without a new design."""
    target='research/v3/schema-clean/fwd1.txt'
    original=(lab.ROOT/target).read_text()
    old='- Sprint when making attacking runs, conserve stamina when tracking back'
    new=('- Use current stamina (not the Stamina skill): below 40%, do not sprint; '
         'from 40% through 70%, sprint only for a clear scoring run or immediate recovery; '
         'above 70%, sprint only when useful. Use a verified stamina scale (fraction 0..1 '
         'or percent 0..100); if unclear, do not guess. Low stamina alone must not veto '
         'a close, clear shot.')
    assert original.count(old)==1
    candidate=original.replace(old,new)
    output=HERE/'candidate/fwd1-energy-v1.txt'
    output.write_text(candidate)
    (HERE/'candidate/fwd1-energy-v1.patch').write_text(patch_for(target,original,candidate,context=2))
    manifest={
        'id':'P02-fwd1-energy-v1','parentHypothesis':'C02',
        'status':'queued_only_not_inferred_not_fitness_tested',
        'change':'Only the original FWD1 sprint instruction; independent of P01',
        'promptBeforeSha256':lab.file_sha(lab.ROOT/target),'promptAfterSha256':lab.file_sha(output),
        'promptBytesBefore':len(original.encode()),'promptBytesAfter':len(candidate.encode()),
        'modelId':'global.amazon.nova-2-lite-v1:0','formation':'1-1-2',
        'freshModelCalls':0,'fitnessResult':None,'eligibleForPromotion':False,
        'thresholdStatus':'Research thresholds, not measured engine constants',
        'shotAccuracyEffect':None,'latencyImprovement':None,
        'physicalContractGap':'Live fractional stamina observed; runtime metadata does not yet explicitly label its scale for the model',
        'rollback':{'prompt':target,'promptSha256':lab.file_sha(lab.ROOT/target),
                    'modelId':'global.amazon.nova-2-lite-v1:0','requireFreshFitness':True},
        'requiredEvidence':['Same-input original/P02 full responses, verified units, both sides, repeated trials',
                            'Tired open-shot and safe-pass positives retained; unnecessary low-energy sprint reduced',
                            'Mid-energy decisive recovery and fresh useful run retained; no stale possession actions',
                            'Full-command p50/p95 and timely useful response rate; longer prompt may increase latency',
                            'Native/readback and fresh Fitness 5/5 before considering a stable live cohort'],
        'doNotBundle':['P01 shot wording','model switch','long-pass policy','D01 timing','formation changes']}
    (HERE/'candidate/energy-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def prepare():
    prepare_energy()
    target='research/v3/schema-clean/fwd1.txt'
    original=(lab.ROOT/target).read_text()
    old='- SHOOT whenever you have the ball within shooting range (~25 units from goal)'
    new='- SHOOT only after the current-possession and close, clear-lane checks below; distance alone is insufficient'
    assert original.count(old)==1
    candidate=original.replace(old,new)
    (HERE/'candidate/fwd1-shot-priority-v1.txt').write_text(candidate)
    (HERE/'candidate/fwd1-shot-priority-v1.patch').write_text(patch_for(target,original,candidate))
    timing_before=(lab.ROOT/'fast_path_v2/main.py').read_text()
    timing_after=(HERE/'candidate/main.py').read_text()
    (HERE/'candidate/fwd2-timing.patch').write_text(patch_for('fast_path_v2/main.py',timing_before,timing_after))
    baseline=json.loads((lab.V3/'cohort-setup-20261025.json').read_text())
    live=json.loads((HERE/'results/move-latency-audit.json').read_text())['latestLiveUpdate']
    assert live['p01']['eligibleForPromotion'] is False
    assert lab.file_sha(lab.ROOT/target)==baseline['agents']['fwd1']['promptSha256']
    manifest={
        'id':'P01-fwd1-shot-priority-v1','status':live['p01']['status'],
        'liveScreeningEvidence':{'sourceCommit':live['sourceCommit'],
                                'path':'research/v3/ranked-batch-13.json',
                                'rawReceiptsRegraded':False,
                                'nextAction':'Retrieve failed-screen receipts; do not repeat or install unchanged P01'},
        'sourceBaseline':'research/v3/cohort-setup-20261025.json',
        'sourceBaselineSha256':lab.file_sha(lab.V3/'cohort-setup-20261025.json'),
        'change':'FWD1 prompt only: remove conflicting distance-only instruction; no new ownership field requirement',
        'candidatePrompt':'research/v3/model-prompt-lab/candidate/fwd1-shot-priority-v1.txt',
        'promptBeforeSha256':lab.file_sha(lab.ROOT/target),
        'promptAfterSha256':lab.file_sha(HERE/'candidate/fwd1-shot-priority-v1.txt'),
        'modelId':'global.amazon.nova-2-lite-v1:0','formation':'1-1-2',
        'unchangedRoles':['GK13 Nova2Lite','DEF19 Nova2Lite','MID15 Nova2Lite','FWD2 stance rev9 source931af03'],
        'freshModelCalls':None,'newModelCallsByResearch':0,'fitnessResult':None,'eligibleForPromotion':False,
        'rollback':{'fwd1Version':'16','promptFile':target,'promptSha256':lab.file_sha(lab.ROOT/target),
                    'modelId':'global.amazon.nova-2-lite-v1:0','requireFreshFitness':True},
        'gates':['Same-input baseline/candidate FWD1 inference: 24 synthetic and 2 observed inputs, 3 repeats, interleaved, isolated allowed idle window',
                 '100% strict command schema; zero illegal ownership actions; clear-shot and safe-pass positive controls retained',
                 'Usable decisions no worse than baseline in any scenario family; full-command p95 <= 1.10 * baseline',
                 'No risky receiver/blocked pass lane in synthetic checks; no late/incomplete candidate responses under an independently verified deadline',
                 'Exact candidate readback and native contract, then fresh Fitness 5/5 before any ranked promotion',
                 'Human transfer to live chat; stable owner-sized cohort at a boundary, never change a running series'],
        'rejectedBeforeInference':{'id':'ownership-guard-draft','reason':'Two captured physical inputs lack possessionTeamCode and hasBall; forcing explicit ownership risks disabling attack',
                                  'evidence':'results/input-contract.json'},
        'queuedNotBundled':[
            {'id':'P02','change':'FWD1 current-energy sprint instruction only',
             'status':'queued independently; no inference or Fitness; thresholds uncalibrated',
             'manifest':'research/v3/model-prompt-lab/candidate/energy-manifest.json'},
            {'id':'M01','change':'Micro FWD1 model-only with unchanged M8 prompt',
             'modelFrom':'global.amazon.nova-2-lite-v1:0','modelTo':'amazon.nova-micro-v1:0',
             'status':'requires same-prompt inference first; selector20/20 is not this configuration'},
            {'id':'D01','change':'FWD2 opt-in timing patch, TRACE_TIMING=1',
             'status':'local byte-equivalence tested only; independent diagnostic, not bundled with P01',
             'patch':'research/v3/model-prompt-lab/candidate/fwd2-timing.patch'}]}
    (HERE/'candidate/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Readable tables use the exact generated JSON as the source of every number.
    report=json.loads((HERE/'results/comparison.json').read_text())
    rows=['# Offline model/prompt comparison — 25 October 2026','',
          'Current status: live P01 paired screening was reported FAILED and P01 was not installed. '
          'Raw screening receipts are not available locally; see DECISION_LATENCY.ru.md. '
          'The archived comparison below is a different evidence set.','',
          '155 archived responses; **zero new inference calls**. 109 full responses are regraded; '
          '40 selector commands are reconstructed; six FWD1 format results rely on the saved full-message audit. '
          'The latter receipt intentionally omits full assistant text.','',
          'Validity = saved command schema (or the selector index contract). Usable = valid AND agrees with '
          'the scenario’s tactical label. Labels are hypotheses, not physical football quality. '
          'p50/p95 use type-7 interpolation; n is small and there is one response per case, without independent repetitions. '
          'The 20 selector rows comprise eight underlying scenarios with cyclic option orders.','',
          '## Full recorded groups','',
          '| Prompt | Role | Model | n | Valid | Usable | p50 / p95 ms | Timing boundary |',
          '|---|---|---|---:|---:|---:|---:|---|']
    for g in report['groups']:
        rows.append(f"| {g['prompt']} | {g['role']} | {g['model']} | {g['n']} | {g['contractValid']}/{g['n']} | {g['usableDecision']}/{g['n']} | {g['latencyMs']['p50']:g} / {g['latencyMs']['p95']:g} | {g['metric']} |")
    rows += ['', '## Prompt revisions on the SAME 21 cases', '',
             'Five stale-context cases added in v2/v3 are excluded here to preserve paired case coverage. '
             'Calls were historical sequential runs; timing changes are not controlled causal effects.', '',
             '| Role / model | Revision | n | Valid | Usable | p50 / p95 ms |',
             '|---|---|---:|---:|---:|---:|']
    for g in report['pairedPromptGroups']:
        rows.append(f"| {g['role']} / {g['model']} | {g['prompt']} | {g['n']} | {g['contractValid']}/{g['n']} | {g['usableDecision']}/{g['n']} | {g['latencyMs']['p50']:g} / {g['latencyMs']['p95']:g} |")
    rows += ['', '## Decisions and missing coverage', '',
             '- GK/DEF/MID: no matched multi-model screen on current prompts. The three prompt rewrites do not qualify. No model recommendation by role can be inferred from FWD2 results.',
             '- FWD1 current M8 prompt: Nova2 has 3/3 valid, 2/3 usable; Haiku 2/3 valid, 2/3 usable. Three cases do not justify switching.',
             '- FWD1 selector: Micro model p50/p95 = 259/372 ms; Nova2 = 393.5/507.8 ms. Full Harness p50/p95 = 1116/2787.35 vs 2061/4651.4 ms. Maxima 32054 and 32247 ms are retained, not dropped as presumed cold starts.',
             '- Selector facts include heuristicScore, option reason and a tactics mode that the instruction directly maps to actions. 20/20 measures rule-following, not independent tactical quality. Constant index0 already passes 12/20. Future selector tests must remove answer hints and permute options (see existing decision_eval.py permutation_cases).',
             '- FWD2 compact screen: Micro is fastest, but only 1/9 usable; Sonnet 3/9; Nova2 and Haiku 0/9. Current FWD2 is deterministic and none of these is a justified replacement.',
             '- Stale-context PASS repeats in DEF/MID/FWD1 in both r1-v2/v3 survive as syntactically valid mistakes. A prompt guard is a testable hypothesis, not a demonstrated fix to the live M8.',
             '- Fast invalid replies do not count as good latency. results/comparison.json includes usable-only latency, evaluable-decision denominators and the original stricter policy-gate results.',
             '- All unmeasured role/model/prompt cells remain not_measured with null percentiles in this archived coverage matrix. Live P01 screening of a subset is tracked separately; its receipts are not embedded here.', '',
             'Sources, source/prompt hashes, per-case recomputed failures, quantile definition and all coverage cells: [comparison.json](results/comparison.json). '
             'Replay: `python3 research/v3/model-prompt-lab/lab.py`.']
    (HERE/'COMPARISON.md').write_text('\n'.join(rows)+'\n')


if __name__=='__main__':prepare()
