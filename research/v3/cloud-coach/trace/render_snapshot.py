"""Render a recorded input snapshot, not a game screenshot or simulated outcome.

Raw inputs/outputs must stay private under .local. No network or game changes.
"""
import argparse
import html
import json
import math
from pathlib import Path


def finite(v):
    return type(v) in (int, float) and math.isfinite(v)


def points(record):
    frame = record.get('frame')
    if frame not in ('keeper_reference_xz', 'documented_xy', 'documented_xy_3d'):
        raise ValueError('Unknown coordinate frame; do not invent a reconstruction')
    rows = record.get('players', [])
    ids = [(p.get('teamCode'), p.get('agentId')) for p in rows]
    expected = {(t, 'agentId_'+str(i)) for t in ('home', 'away') for i in range(5)}
    if len(rows) != 10 or set(ids) != expected:
        raise ValueError('Incomplete or ambiguous player identities')
    result = []
    for p in rows:
        pos = p.get('position') or {}
        if not all(finite(pos.get(k)) for k in ('x', 'y')):
            raise ValueError('Unknown player position')
        result.append((pos['x'], pos['y']))
    pos = record.get('ball', {}).get('position') or {}
    ykey = 'z' if frame == 'keeper_reference_xz' else 'y'
    if not all(finite(pos.get(k)) for k in ('x', ykey)):
        raise ValueError('Unknown ball ground position')
    return result + [(pos['x'], pos[ykey])]


def render(record, bounds=None):
    coords = points(record)
    if bounds is None:
        xs, ys = zip(*coords)
        bounds = (min(xs), max(xs), min(ys), max(ys))
    x0, x1, y0, y1 = bounds
    if not all(finite(v) for v in bounds) or x1 < x0 or y1 < y0:
        raise ValueError('Invalid coordinate bounds')
    padx, pady = max((x1-x0)*.08, .5), max((y1-y0)*.12, .5)
    x0 -= padx; x1 += padx; y0 -= pady; y1 += pady
    scale = min(900/(x1-x0), 460/(y1-y0))
    def project(x, y):
        return 60+(x-x0)*scale, 560-(y-y0)*scale
    esc = lambda x: html.escape(str(x), quote=True)
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="740" viewBox="0 0 1100 740">',
             '<rect width="1100" height="740" fill="#101c23"/>',
             '<g font-family="sans-serif" fill="#eff6f8">',
             '<text x="35" y="38" font-size="23">Recorded input snapshot · NOT gameplay footage</text>',
             f'<text x="35" y="66" font-size="16">Game time {esc(record.get("gameTime"))} · score {esc(record.get("score", {}).get("home"))}:{esc(record.get("score", {}).get("away"))} · {esc(record.get("playMode"))} · frame {esc(record.get("frame"))}</text>',
             '<rect x="45" y="90" width="970" height="490" fill="#153c31" stroke="#8bab9a"/>']
    # No surveyed pitch or goalposts are invented from goalkeeper positions.
    for x, y, label in [(x0, y0, f'x={x0:.2f}, y={y0:.2f}'), (x1, y1, f'x={x1:.2f}, y={y1:.2f}')]:
        px, py = project(x, y)
        lines.append(f'<text x="{px:.2f}" y="{max(110,min(574,py)):.2f}" font-size="11">{esc(label)}</text>')
    own = 'home' if record.get('teamId') == 0 else 'away' if record.get('teamId') == 1 else None
    if own is None:
        raise ValueError('Unknown observer team')
    for p, (x, y) in zip(record['players'], coords[:-1]):
        px, py = project(x, y); color = '#65ef8c' if p['teamCode'] == own else '#f28ad1'
        label = str(int(p['agentId'].split('_')[-1])+1)
        lines += [f'<circle cx="{px:.2f}" cy="{py:.2f}" r="14" fill="{color}" stroke="#fff"/>',
                  f'<text x="{px:.2f}" y="{py+5:.2f}" text-anchor="middle" fill="#101c23" font-size="15">{label}</text>',
                  f'<text x="{px+17:.2f}" y="{py-13:.2f}" font-size="11">S={esc(p.get("stamina"))} {esc(p.get("currentAction") or "?")}</text>']
    bx, by = project(*coords[-1]);lines.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="6" fill="#fff" stroke="#000" stroke-width="2"/>')
    ball = record.get('ball', {})
    owner = ball.get('possessionTeamCode')
    agent = ball.get('possessionAgentId')
    ownership = f'{owner}/{agent}' if owner in ('home','away') and agent else 'unknown team-qualified owner'
    intention = json.dumps(record.get('ownIntent', []), ensure_ascii=True)
    lines += [f'<text x="35" y="610" font-size="15">Green: own team. Pink: opponent. UI number = playerId + 1. Stamina S is raw, not assumed percent.</text>',
              f'<text x="35" y="636" font-size="15">Ball ownership: {esc(ownership)}. Own attack: {"+x" if own == "home" else "-x"}. Goals not surveyed.</text>',
              f'<text x="35" y="662" font-size="12">MID intent: {esc(intention)}</text>',
              '<text x="35" y="690" font-size="14">Sampled positions do not establish pass completion, shot accuracy or the cause of a goal.</text>',
              '<text x="35" y="718" font-size="14">Raw-coordinate plot: this rectangle is NOT a measured pitch boundary.</text>',
              '</g></svg>']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--index', type=int, default=0)
    args = parser.parse_args()
    if any('.local' not in p.resolve().parts for p in (args.input, args.output)):
        raise ValueError('Raw match snapshots and renders must remain in private .local')
    records = json.loads(args.input.read_text())
    if not isinstance(records, list):
        raise ValueError('Expected a list of extracted MID_TRACE records')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    selected = records[args.index]
    coords = []
    for record in records:
        if record.get('frame') != selected.get('frame'):
            continue
        try:
            coords.extend(points(record))
        except ValueError:
            continue
    if not coords:
        raise ValueError('No valid points in the selected coordinate frame')
    xs, ys = zip(*coords)
    args.output.write_text(render(selected, (min(xs), max(xs), min(ys), max(ys))))


if __name__ == '__main__':
    main()
