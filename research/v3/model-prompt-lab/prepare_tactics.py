#!/usr/bin/env python3
"""Prepare two independent queued prompt diffs. Never applies or promotes them."""
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent


def prepare():
    bundle = json.loads((V3 / 'recovery/bundle.json').read_text())
    specs = [
        ('P03', 'def', 'def-single-press-v1', 'C03',
         '- PRESS_BALL when an opponent with the ball enters your zone',
         '- PRESS_BALL against an opponent ball carrier in your defensive zone only when you are the strictly closest suitable outfield teammate; otherwise shield the central route to your goal or MARK the dangerous runner.',
         ['MID closer: DEF shields/marks instead of joining press',
          'DEF closest in defensive zone: recovery remains available',
          'Own possession: safe distribution, never PRESS',
          'Equal distance, HOME/AWAY, low stamina and missing state',
          'Joint same-tick team decisions and physical defensive coverage']),
        ('P04', 'mid', 'mid-pass-lane-v1', 'C02',
         '- MID (player 2): prioritize PASS to an open forward (player 3 or 4).',
         '- MID (player 2): prioritize PASS to an open forward (player 3 or 4) with a clear passing lane; when neither forward offers a safe pass, recycle to an open defender with a clear lane. If no pass is safe, use the existing shot or movement rules.',
         ['Open forward with blocked lane: do not force that pass',
          'Free forward and clear lane: keep the progressive pass',
          'Both forwards marked, defender available: recycle',
          'No safe pass, clear shot: do not suppress finishing',
          'No safe pass/shot: improve position without inventing a receiver',
          'HOME/AWAY, possession changes, stale MOVE history, physical pass outcomes'])]
    manifests = []
    for ident, role, name, parent, old, new, checks in specs:
        source = V3 / 'schema-clean' / (role + '.txt')
        before = source.read_text()
        sha = hashlib.sha256(before.encode()).hexdigest()
        if sha != bundle['roles'][role]['promptSha256'] or before.count(old) != 1:
            raise ValueError('Baseline changed; review candidate before regeneration: ' + role)
        after = before.replace(old, new)
        target = HERE / 'candidate' / (name + '.txt')
        target.write_text(after)
        path = 'research/v3/schema-clean/' + role + '.txt'
        patch = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                           fromfile='a/' + path, tofile='b/' + path, n=2))
        target.with_suffix('.patch').write_text(patch)
        manifests.append({'id': ident, 'parentHypothesis': parent, 'role': role,
                          'status': 'queued_review_only; no inference or Fitness',
                          'source': path, 'baselineVersion': bundle['roles'][role]['sourceVersion'],
                          'promptBeforeSha256': sha,
                          'promptAfterSha256': hashlib.sha256(after.encode()).hexdigest(),
                          'promptBytesBefore': len(before.encode()), 'promptBytesAfter': len(after.encode()),
                          'modelIdUnchanged': 'global.amazon.nova-2-lite-v1:0',
                          'patch': 'research/v3/model-prompt-lab/candidate/' + name + '.patch',
                          'formationUnchanged': '1-1-2', 'otherRolesUnchanged': True,
                          'freshModelCalls': 0, 'pairedPlanReady': False, 'fitnessResult': None,
                          'eligibleForPromotion': False, 'requiredScenarioFamilies': checks,
                          'limitations': ['Static prompt defect/risk, not diagnosed cause of live losses',
                                          'Longer prompt; latency improvement unmeasured',
                                          'Existing role suite alone does not validate this new tactical rule',
                                          'No newly required possession field or coordinate scale',
                                          'Do not stack with P01, P02, model or deployment changes'],
                          'rollback': {'promptFile': path, 'promptSha256': sha,
                                       'freshFitnessRequired': True}})
    (HERE / 'candidate/tactical-manifests.json').write_text(json.dumps(manifests, indent=2) + '\n')
    return manifests


if __name__ == '__main__':
    print(json.dumps({'prepared': [r['id'] for r in prepare()], 'applied': 0, 'calls': 0}))
