"""Prepare one MID identity clarification; do not modify the canonical prompt."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
source = ROOT / 'research/v3/schema-clean/mid.txt'
baseline = source.read_text()
bundle = json.loads((ROOT / 'research/v3/recovery/bundle.json').read_text())
before_sha = hashlib.sha256(baseline.encode()).hexdigest()
assert before_sha == bundle['roles']['mid']['promptSha256']
identity = '''## Player and team identity — apply before tactics
- Your side is the input teamId: 0 means home, 1 means away. Find YOUR player using both that teamCode and agentId_2. Both teams reuse agentId_0 through agentId_4; never identify a player by agentId alone or assume your team is home.
- When possessionTeamCode or possessionTeamId is supplied, combine it with possessionAgentId or possessionPlayerId to identify the ball owner. Use hasBall when supplied as supporting evidence. A different team's agentId_2 is not you. Do not choose the first matching agentId from the players array. Missing team ownership fields must not be fabricated.
- If the explicit owner is YOUR side's player 2, you have the ball: do not PRESS_BALL, MARK, INTERCEPT or FOLLOW_PLAYER. If the explicit owner is on the other side, do not PASS or SHOOT.
- PASS target_player_id is the numeric agentId suffix of a teammate on YOUR side, not the displayed shirt number. Select the teammate using both teamCode and agentId; exclude yourself.

'''
anchor = '## Your Role — Midfielder\n'
assert baseline.count(anchor) == 1
candidate = baseline.replace(anchor, identity + anchor)
(HERE / 'mid-identity-p05.txt').write_text(candidate)
(HERE / 'mid-identity-p05.patch').write_text(''.join(difflib.unified_diff(
    baseline.splitlines(True), candidate.splitlines(True),
    fromfile='a/research/v3/schema-clean/mid.txt',
    tofile='b/research/v3/schema-clean/mid.txt', n=2)))
manifest = {
    'id': 'P05-MID-identity', 'status': 'prepared-not-registered',
    'scope': 'One identity/ownership interpretation clarification; no tactical thresholds or coordinate changes',
    'promptBeforeSha256': before_sha,
    'promptAfterSha256': hashlib.sha256(candidate.encode()).hexdigest(),
    'modelUnchanged': 'global.amazon.nova-2-lite-v1:0',
    'otherRolesUnchanged': True, 'formation': '1-1-2',
    'evidence': 'baseline-pass-screen; explicit AWAY ownership received defensive responses in synthetic native calls',
    'testPlan': 'plan.json; same 20 cases, one fresh own session each; compare explicit-ownership contradictions first',
    'promotion': False,
    'rollback': 'Canonical MID15 unchanged prompt/model, exact current-account binding, fresh Fitness5/5',
    'limitations': ['Synthetic native decision screen, not match behavior',
                    'No hard requirement for new possession fields',
                    'Marked-receiver and pass-lane tactics are outside this identity-only change',
                    'Cold/first response deadline remains a separate gate'],
}
(HERE / 'mid-identity-p05.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Prepared P05 identity-only prompt; canonical Baseline unchanged')
