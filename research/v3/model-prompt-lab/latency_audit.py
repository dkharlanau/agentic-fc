#!/usr/bin/env python3
"""Recompute MOVE/latency evidence from saved files and a pinned local Git object.

No network, model calls or changes to the live checkout. Export only aliases,
counts, timing boundaries and hashes; no raw game state or assistant reasoning.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

import lab

LIVE_COMMIT = '3cdf5a76e5e87b103c631f829af80983f6991667'
UPDATE_COMMIT = 'cbde2741594864155feb48eb289ff4e35ef0be04'
HERE = Path(__file__).resolve().parent


def build():
    sources = []

    def read(name, commit=None):
        path = 'research/v3/' + name
        raw = (subprocess.check_output(['git', 'show', commit + ':' + path], cwd=lab.ROOT)
               if commit else (lab.ROOT / path).read_bytes())
        sources.append({'path': path, 'gitCommit': commit,
                        'sha256': hashlib.sha256(raw).hexdigest()})
        return json.loads(raw) if name.endswith('.json') else raw.decode()

    fresh = []
    specs = [('possession-probes.json', 'fwd2'),
             ('fwd1-direct-model-probes.json', 'fwd1'),
             ('fwd1-sonnet-probes.json', 'fwd1')]
    for filename, role in specs:
        data = read(filename)
        samples = data['results'] + ([data['contractCandidate']] if 'contractCandidate' in data else [])
        for i, row in enumerate(samples):
            model = row.get('model', row.get('modelLabel'))
            model = ('nova2' if 'nova' in model.lower() else
                     'haiku' if 'haiku' in model.lower() else 'sonnet')
            command_array = row.get('responseArray', row.get('response'))
            schema_valid = not lab.command_errors(json.dumps(command_array), role)
            full_format = row.get('jsonOnlyPassed', row.get('fullResponseJsonOnly', row.get('formatPassed')))
            expected = row.get('expectedCommandCategories', [row.get('expectedCategory')])
            category = command_array[0]['commandType'] in expected
            prompt = row.get('prompt', data.get('systemPrompt'))
            prompt_sha = lab.file_sha(lab.V3 / prompt)
            if row.get('promptSha256', prompt_sha) != prompt_sha:
                raise ValueError('Archived prompt hash mismatch: ' + filename)
            valid = schema_valid and full_format is True
            fresh.append({'source': filename, 'sampleOrdinal': i + 1, 'role': role,
                          'model': model, 'prompt': prompt, 'promptSha256': prompt_sha, 'case': row['case'],
                          'action': command_array[0]['commandType'], 'strictValid': valid,
                          'formatEvidence': 'saved full-message audit; full text not re-parsed',
                          'categoryAgreement': category, 'usable': valid and category,
                          'latencyMs': row['reportedPlaygroundLatencyMs'],
                          'inputTokens': row['inputTokens'], 'outputTokens': row['outputTokens']})
    groups = defaultdict(list)
    for row in fresh:
        groups[(row['role'], row['model'], row['prompt'])].append(row)
    comparisons = []
    for (role, model, prompt), rows in sorted(groups.items()):
        comparisons.append({'role': role, 'model': model, 'prompt': prompt,
                            'n': len(rows), 'valid': sum(r['strictValid'] for r in rows),
                            'usable': sum(r['usable'] for r in rows),
                            'reportedPlaygroundMs': lab.distribution([r['latencyMs'] for r in rows]),
                            'over1000MsReferenceCount': sum(r['latencyMs'] > 1000 for r in rows)})

    histories = []
    for revision in ('v2', 'v3'):
        data = read('role-package-r1/model-eval-' + revision + '.json')
        by_id = {r['id']: r for r in data['results']}
        for role in lab.ROLES:
            key = role + '-ambiguous-owner'
            a, b = by_id[key], by_id[key + '-stale-context']
            def summary(r):
                parsed = lab.parse_command(r['output'])
                return {'inputTokens': r['usage']['inputTokens'], 'wallMs': r['requestWallMs'],
                        'strictValid': not lab.command_errors(r['output'], role),
                        'originalPolicyGatePassed': not r['errors'],
                        'action': parsed['commandType'] if parsed else None}
            histories.append({'revision': revision, 'role': role,
                              'withoutHistory': summary(a), 'withFourOldPairs': summary(b),
                              'inputTokenRatio': round(b['usage']['inputTokens'] / a['usage']['inputTokens'], 3)})

    gk = read('allcash-benchmark/gk-route.json')
    native = []
    for row in gk['calls']:
        meta = row['metadata'][0]
        native.append({'ordinal': row['repeat'] + 1,
                       'headersMs': round(row['headersMs'], 3),
                       'firstEventMs': round(row['firstEventMs'], 3),
                       'completeMs': round(row['completeMs'], 3),
                       'reportedModelMs': meta['metrics']['latencyMs'],
                       'wallMinusReportedModelMs': round(row['completeMs'] - meta['metrics']['latencyMs'], 3),
                       'strictValid': not lab.command_errors(row['text'], 'gk'),
                       'inputTokens': meta['usage']['inputTokens'],
                       'outputTokens': meta['usage']['outputTokens'],
                       'firstTextMs': None, 'messageStopMs': None, 'serverApplyMs': None})
    fast = read('allcash-benchmark/fast-route.json')
    fast_rows = [{'ordinal': r['repeat'] + 1, 'headersMs': round(r['headersMs'], 3),
                  'completeMs': round(r['completeMs'], 3),
                  'bodyReadAfterHeadersMs': round(r['completeMs'] - r['headersMs'], 3)} for r in fast['calls']]

    batch = read('ranked-batch-12.json', LIVE_COMMIT)
    batch_rows = []
    for game in batch['games']:
        facts = game['rawReportFacts']
        counts = facts.get('teamCommandCounts')
        total = facts['teamCommands']
        # An absent histogram is unknown. With a recorded histogram, an absent
        # action is zero only when its full counts reconcile to the total.
        complete = counts is not None and sum(counts.values()) == total
        def count(action):
            return counts.get(action, 0) if complete else None
        move = count('MOVE_TO')
        batch_rows.append({'alias': game['alias'], 'side': game['side'],
                           'scoreFor': game['scoreFor'], 'scoreAgainst': game['scoreAgainst'],
                           'teamReportMeanMs': facts['teamAverageLatencyMs'],
                           'commands': total, 'histogramReconciled': complete,
                           'movePct': round(100 * move / total, 3) if move is not None and total else None,
                           'passCount': count('PASS'), 'shootCount': count('SHOOT'),
                           'perInvocationP50Ms': None, 'perInvocationP95Ms': None})
    bundle = read('recovery/bundle.json')
    configs = []
    for role, row in bundle['roles'].items():
        c = row['configuration']
        configs.append({'role': role, 'sourceVersion': row['sourceVersion'],
                        'truncation': c['truncation'], 'maxIterations': c['maxIterations'],
                        'timeoutSeconds': c['timeoutSeconds'], 'toolCount': len(c['tools']),
                        'inferenceConfig': c['model']['bedrockModelConfig'].get('inferenceConfig')})
    latest = read('ranked-batch-13.json', UPDATE_COMMIT)
    ongoing = read('ranked-batch-14.json', UPDATE_COMMIT)
    read('ranked-batch-13-analysis.ru.md', UPDATE_COMMIT)
    checkpoint = subprocess.check_output(['git', 'show', UPDATE_COMMIT + ':HANDOFF.md'], cwd=lab.ROOT)
    sources.append({'path': 'HANDOFF.md', 'gitCommit': UPDATE_COMMIT,
                    'sha256': hashlib.sha256(checkpoint).hexdigest()})
    games13 = []
    for i, game in enumerate(latest['games']):
        score = [int(n) for n in game['score'].split('-')]
        shots = [int(n) for n in game['shots'].split('-')]
        on_target = [int(n) for n in game['shotsOnTarget'].split('-')]
        games13.append({'alias': 'batch13-game-' + str(i + 1), 'result': game['result'],
                        'scoreFor': score[0], 'scoreAgainst': score[1],
                        'shotsFor': shots[0], 'shotsAgainst': shots[1],
                        'onTargetFor': on_target[0], 'onTargetAgainst': on_target[1],
                        'teamReportMeanMs': game['teamAverageLatencyMs'],
                        'roleReportMeansMs': game['roleLatencyMs'],
                        'teamCommands': game['teamCommands'], 'actionsReported': game['actions']})
    result_groups = {}
    for result in ('WIN', 'LOSS'):
        rows = [g for g in games13 if g['result'] == result]
        result_groups[result] = {k: sum(g[k] for g in rows) for k in
                                ('shotsFor', 'onTargetFor', 'scoreFor', 'scoreAgainst')}
        result_groups[result]['games'] = len(rows)
    update = {'sourceCommit': UPDATE_COMMIT,
              'p01': {'status': 'rejected_at_paired_screen_reported_by_game_flow',
                      'sourceStatement': latest['preflight']['p01'], 'installed': latest['setup']['p01Installed'],
                      'rawReceiptsAvailableLocally': False, 'testedRequestHashesVerified': False,
                      'caseFailures': None, 'fullResponseP50Ms': None, 'fullResponseP95Ms': None,
                      'numberOfExecutedModelCalls': None, 'independentlyRegraded': False,
                      'eligibleForPromotion': False},
              'batch13': {'games': games13, 'byResultRecomputed': result_groups,
                          'medianOfFiveReportMeansMs': lab.percentile([g['teamReportMeanMs'] for g in games13], .5),
                          'roleMeansOver1000Reference': sum(v > 1000 for g in games13 for v in g['roleReportMeansMs']),
                          'fullResponseP95Ms': None},
              'batch14': {'status': ongoing['status'], 'completedGames': ongoing['completedGames'],
                          'target': ongoing['targetCompletedGames'], 'setup': ongoing['setup']},
              'nextStep': 'Existing exact trace and P01 receipt export; no repeat P01 unchanged or candidate series'}
    return {'kind': 'Offline archived MOVE/latency audit; no fresh inference',
            'quantiles': 'Hyndman-Fan type 7; tiny, unequal samples, no causal model ranking',
            'deadline': {'1000MsUsedOnlyAsReference': True, 'verifiedGameEnforcement': None},
            'sources': sources, 'archivedProbeRows': fresh, 'probeComparisons': comparisons,
            'historyPairs': histories,
            'nativeGk': {'timingBoundary': gk['kind'], 'sameSession': True, 'calls': native,
                         'limit': 'Wall-minus-model is an unlocalized residual, not network latency. Both full texts violate strict JSON.'},
            'modelFreeFwd2': {'timingBoundary': fast['kind'], 'calls': fast_rows,
                             'subsequentCallMs': lab.distribution([r['completeMs'] for r in fast_rows[1:]]),
                             'limit': 'First call is observed; infrastructure cold-start causation unproven.'},
            'batch12': {'sourceCommit': LIVE_COMMIT, 'completedGames': len(batch_rows),
                        'additionalIncomingMatchesExcluded': True, 'games': batch_rows},
            'savedOriginalHarnessConfiguration': configs,
            'latestLiveUpdate': update,
            'currentLiveReadback': None, 'modelCallsExecuted': 0, 'promotionEligible': False}


if __name__ == '__main__':
    output = HERE / 'results/move-latency-audit.json'
    result = build()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'probes': len(result['archivedProbeRows']),
                      'historyPairs': len(result['historyPairs']),
                      'freshCalls': 0, 'output': str(output)}))
