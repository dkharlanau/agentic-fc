"""Offline, descriptive tournament decision audit. Never calls AWS or matchmaking."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def points(row):
    return 3 if row['goalsFor'] > row['goalsAgainst'] else int(row['goalsFor'] == row['goalsAgainst'])


def summarize(rows):
    complete = [r for r in rows if r.get('shotsFor') is not None and r.get('shotsAgainst') is not None]
    gf, ga = (sum(r[k] for r in rows) for k in ('goalsFor', 'goalsAgainst'))
    wins = sum(points(r) == 3 for r in rows)
    draws = sum(points(r) == 1 for r in rows)
    ahead = [r for r in complete if r['shotsFor'] > r['shotsAgainst']]
    return {
        'reports': [r['id'] for r in rows], 'played': len(rows),
        'wins': wins, 'draws': draws, 'losses': len(rows) - wins - draws,
        'points': 3 * wins + draws, 'ppg': (3 * wins + draws) / len(rows) if rows else None,
        'goalsFor': gf, 'goalsAgainst': ga, 'shotCoverage': len(complete),
        'shotsForKnown': sum(r['shotsFor'] for r in complete),
        'shotsAgainstKnown': sum(r['shotsAgainst'] for r in complete),
        'scoreless': sum(r['goalsFor'] == 0 for r in rows),
        'zeroShotReports': [r['id'] for r in complete if r['shotsFor'] == 0],
        'oneGoalLosses': sum(r['goalsAgainst'] - r['goalsFor'] == 1 for r in rows),
        'medianGoalDifference': median([r['goalsFor'] - r['goalsAgainst'] for r in rows]) if rows else None,
        'largestWinGoalShare': max([r['goalsFor'] for r in rows if points(r) == 3], default=0) / gf if gf else None,
        'shotAdvantage': {'played': len(ahead), 'wins': sum(points(r) == 3 for r in ahead),
                          'draws': sum(points(r) == 1 for r in ahead), 'losses': sum(points(r) == 0 for r in ahead)},
    }


def build():
    rows = json.loads((HERE / 'matches.json').read_text())['matches']
    lookup = {r['id']: r for r in rows}
    if len(lookup) != len(rows):
        raise ValueError('Duplicate report IDs')
    if set(lookup) != {f'live-{n:02d}' for n in range(1, 81)}:
        raise ValueError('Frozen audit requires the live01..80 snapshot; do not silently extend its window')
    shot_audit = json.loads((HERE / 'shots-analysis.json').read_text())
    if shot_audit['sourceSha256'] != digest(HERE / 'matches.json') or shot_audit['throughReport'] != 'live-80':
        raise ValueError('Shot analysis is stale relative to the frozen match snapshot')
    select = lambda a, b: [lookup[f'live-{n:02d}'] for n in range(a, b + 1)]
    groups = {
        'earlyM8HistoricalWindow': select(28, 38),
        'earlyM8IncludingNextAttributedLoss': select(28, 38) + [lookup['live-41']],
        'mixed53to62': select(53, 62),
        'stableM8': select(63, 72),
        'positionV14Planned': select(74, 78),
        'positionV14IncludingIncoming': select(73, 79),
        'formation121Partial': [lookup['live-80']],
        'historical121BeforePartial': select(22, 27) + [lookup['live-42'], lookup['live-46']],
    }
    summaries = {}
    for name, subset in groups.items():
        summaries[name] = summarize(subset)
        summaries[name]['bySide'] = {side: summarize([r for r in subset if r.get('side') == side])
                                    for side in ('home', 'away')}
        summaries[name]['recordedSetupCounts'] = dict(Counter(r['setup'] for r in subset))
    # Standardisation controls only the recorded side, not opponent strength or timing.
    side_standardized = {}
    for name in ('earlyM8HistoricalWindow', 'stableM8', 'positionV14Planned'):
        s = summaries[name]['bySide']
        side_standardized[name] = (sum(s[x]['ppg'] for x in ('home', 'away')) / 2
                                  if all(s[x]['played'] for x in ('home', 'away')) else None)
    early = groups['earlyM8HistoricalWindow']
    recent = groups['stableM8']
    keys = {(r.get('opponent'), r['side']) for r in early} & {(r.get('opponent'), r['side']) for r in recent}
    common = [{'opponent': name, 'side': side,
               'early': summarize([r for r in early if (r.get('opponent'), r['side']) == (name, side)]),
               'recent': summarize([r for r in recent if (r.get('opponent'), r['side']) == (name, side)])}
              for name, side in sorted(keys)]
    batch_reconciliation = {}
    source_files = ['matches.json', 'shots-analysis.json', 'side-audit-20261024.json',
                    'final-setup-20261024.json', 'recovery/bundle.json']
    for n in range(1, 5):
        path = f'ranked-batch-{n:02d}.json'
        source_files.append(path)
        batch = json.loads((HERE / path).read_text())
        subset = [lookup[x] for x in batch['reports']]
        s = summarize(subset)
        fields = ('played', 'wins', 'draws', 'losses', 'points', 'goalsFor', 'goalsAgainst')
        deltas = {k: batch['after'][k] - batch['before'][k] for k in fields}
        if any(deltas[k] != s[k] for k in fields):
            raise ValueError(f'Unreconciled batch {n}')
        batch_reconciliation[path] = {'completed': len(subset), 'target': batch['targetCompleted'],
                                      'status': batch['status'], 'counterDelta': deltas, 'matchesExactly': True}
    manifest = json.loads((HERE / 'final-setup-20261024.json').read_text())
    bundle = json.loads((HERE / 'recovery/bundle.json').read_text())
    for role, entry in manifest['roles'].items():
        source_files.append(str(Path(entry['promptFile']).relative_to('research/v3')))
        config = bundle['roles'][role]['configuration']
        if digest(ROOT / entry['promptFile']) != entry['promptSha256']:
            raise ValueError(f'Prompt hash mismatch: {role}')
        if hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != entry['configurationSha256']:
            raise ValueError(f'Config hash mismatch: {role}')
        if entry['exportSourceVersion'] != bundle['roles'][role]['sourceVersion']:
            raise ValueError(f'Export metadata mismatch: {role}')
    if digest(HERE / 'recovery/bundle.json') != manifest['recovery']['bundleSha256']:
        raise ValueError('Recovery bundle hash mismatch')
    complete = [r for r in rows if all(r.get(k) is not None for k in
                ('shotsFor', 'shotsAgainst', 'shotsOnTargetFor', 'shotsOnTargetAgainst'))]
    losses = [r for r in recent if points(r) == 0]
    candidates = groups['positionV14Planned']
    return {
        'kind': 'Frozen offline descriptive audit; no causal effect, model ranking or new live result',
        'date': '2026-10-24', 'throughReport': 'live-80', 'reports': len(rows),
        'sourceHashes': {str(Path('research/v3') / p): digest(HERE / p) for p in source_files},
        'analysisScriptSha256': digest(Path(__file__)), 'cohorts': summaries,
        'equalSideWeightPPG': side_standardized,
        'commonOpponentAndSideEarlyVersusRecent': common,
        'stableVersusPositionCommonOpponentNames': sorted({r.get('opponent') for r in recent} & {r.get('opponent') for r in candidates}),
        'sensitivity': {
            'stableWithoutLive69': summarize([r for r in recent if r['id'] != 'live-69']),
            'stableWithoutLowCountLive66And69': summarize([r for r in recent if r['id'] not in ('live-66', 'live-69')]),
            'mixedWithout7to0': summarize([r for r in groups['mixed53to62'] if r['id'] != 'live-57']),
            'stableLossesOutcomeSelected': summarize(losses),
        },
        'reportCounterAudit': {
            'complete': len(complete), 'missing': [r['id'] for r in rows if r not in complete],
            'allCompleteSotEqualsGoalsBothSides': all(r['shotsOnTargetFor'] == r['goalsFor'] and r['shotsOnTargetAgainst'] == r['goalsAgainst'] for r in complete),
            'reportedShots': sum(r['shotsFor'] for r in complete),
            'reportedSot': sum(r['shotsOnTargetFor'] for r in complete),
            'reportedShotsDespiteNoReportedShoot53to62': [r['id'] for r in groups['mixed53to62'] if r.get('shotsFor', 0) > 0 and r.get('commandCounts', {}).get('SHOOT', 0) == 0],
        },
        'batchReconciliation': batch_reconciliation,
        'baselineIntegrity': 'five prompt hashes, five config hashes, export versions and bundle hash verified locally',
        'limitations': ['Early window has no AWAY support; side adjustment is not identifiable.',
                       'Opponent names do not prove identical opponent versions. No pre-match strength covariate.',
                       'Sensitivity exclusions never replace official results; outcome selection is diagnostic only.',
                       'M8 has no captured per-tick input/output/execution chain for these recent matches.',
                       'Latest verified live configuration remains the saved 15:39 UTC snapshot, not a new portal read.'],
    }


if __name__ == '__main__':
    result = build()
    output = HERE / 'tournament-evidence-20261024.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for key, value in result['cohorts'].items():
        print(key, {k: value[k] for k in ('played', 'wins', 'draws', 'losses', 'ppg', 'goalsFor', 'goalsAgainst', 'shotCoverage', 'shotsForKnown', 'shotsAgainstKnown')})
