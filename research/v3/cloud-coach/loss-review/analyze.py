"""Read-only analysis of one recorded match, not a simulator or causal model.

Raw trace inputs and detailed output must remain inside .local. Scores are
observed transitions; gameTime at a score update need not be exact goal time.
"""
import argparse
import json
import math
from pathlib import Path


def finite(x):
    return type(x) in (int, float) and math.isfinite(x)


def analyze(records):
    # Preserve capture chronology, not game clock, which can freeze/reset.
    rows = sorted(records, key=lambda r: r['handlerUnixNs'])
    events, warnings, valid, seen = [], [], [], set()
    previous_score = None
    observed_frame_and_side = None
    for r in rows:
        key = (r.get('handlerUnixNs'), r.get('tick'))
        if key in seen:
            continue
        seen.add(key)
        score = r.get('score', {})
        if any(type(score.get(k)) is not int or score[k] < 0 for k in ('home', 'away')):
            warnings.append('invalid_score')
            continue
        if previous_score is not None:
            delta = {k: score[k]-previous_score[k] for k in ('home','away')}
            if min(delta.values()) < 0:
                raise ValueError('Score decreased: split separate matches before analysis')
            elif sum(delta.values()):
                history = [a for a in valid if a['score'] == previous_score
                           and finite(r.get('gameTime'))
                           and r['gameTime'] >= a['gameTime']]
                prior = [a for a in history if r['gameTime']-a['gameTime'] <= 8]
                for side in ('home','away'):
                    if delta[side]:
                        events.append({'scoringSide':side, 'scoreIncrement':delta[side],
                            'observedScoreTime':r.get('gameTime'),
                            'lastSampleGapSeconds':r['gameTime']-history[-1]['gameTime'] if history else None,
                            'precedingSamples':prior[-4:], 'causalAttribution':None})
        previous_score = dict(score)
        if r.get('playMode') not in ('OPEN_PLAY','PLAY_ON') or not finite(r.get('gameTime')):
            continue
        players = r.get('players', [])
        keys = {(p.get('teamCode'),p.get('agentId')) for p in players}
        expected = {(t,f'agentId_{i}') for t in ('home','away') for i in range(5)}
        if len(players) != 10 or keys != expected:
            continue
        if any(not all(finite(p.get('position',{}).get(k)) for k in ('x','y')) for p in players):
            continue
        own = 'home' if r.get('teamId') == 0 else 'away' if r.get('teamId') == 1 else None
        if own is None or r.get('frame') not in ('keeper_reference_xz','documented_xy','documented_xy_3d'):
            continue
        frame_and_side = (r['frame'], r['teamId'])
        if observed_frame_and_side is not None and frame_and_side != observed_frame_and_side:
            raise ValueError('Mixed coordinate frames or observer teams')
        observed_frame_and_side = frame_and_side
        own_players = {p['agentId']:p for p in players if p['teamCode']==own}
        a,b = (own_players[f'agentId_{i}']['position'] for i in (2,3))
        ball = r.get('ball', {})
        valid.append({'gameTime':r['gameTime'], 'score':dict(score),
            'ball':ball, 'players':players, 'ownIntent':r.get('ownIntent'),
            'reason':r.get('reason'), 'midForwardDistance':math.hypot(a['x']-b['x'],a['y']-b['y']),
            'ownStamina':{str(i):own_players[f'agentId_{i}'].get('stamina') for i in range(5)}})
    counters = {}
    for i in range(5):
        values = [r['ownStamina'][str(i)] for r in valid if finite(r['ownStamina'][str(i)])]
        counters[str(i)] = {'knownSamples':len(values),'below025Samples':sum(v<.25 for v in values)}
    return {'openPlaySamples':len(valid),'ownStamina':counters,
        'midForwardWithin1Samples':sum(r['midForwardDistance']<1 for r in valid),
        'scoreTransitions':events, 'warnings':sorted(set(warnings)),
        'limits':['Sample counts are not time-weighted.',
                  'Missing contact/shot frames cannot establish cause, shooter or pass completion.',
                  'Do not mix policies or opponents when comparing results.',
                  'Distance threshold 1 uses raw coordinates; do not compare different frames.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    for p in (args.input,args.output):
        if '.local' not in p.resolve().parts:raise SystemExit('Raw traces and detailed results must stay under .local')
    result=analyze(json.loads(args.input.read_text()));args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
