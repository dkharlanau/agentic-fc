"""Extract public-safe numbers from a saved, rendered Player Portal AX report.

This reads local evidence only. It does not call AWS, access browser internals,
or establish that a model was invoked or that an issued command was applied.
"""

import argparse
import json
from pathlib import Path
import re


ACTIONS = {
    "Move": "MOVE_TO", "Pass": "PASS", "Shoot": "SHOOT",
    "Press": "PRESS_BALL", "Intercept": "INTERCEPT", "Mark": "MARK",
    "Follow": "FOLLOW_PLAYER", "Clear": "CLEAR_OVERRIDE", "Reset": "RESET",
    "GK Dist": "GK_DISTRIBUTE", "Stance": "SET_STANCE",
    "Slide": "SLIDE_TACKLE", "Slide Tackle": "SLIDE_TACKLE",
}


def parse_report(raw, team, opponent, side, *, allow_missing_stats=False):
    lines = re.findall(r"^\s*(?:[+~]\s*)?\d+ text (.*)$", raw, re.M)
    text = re.sub(r"\s+", " ", " ".join(lines))
    home, away = (team, opponent) if side == "home" else (opponent, team)
    score = re.search(re.escape(home) + r"\s+(\d+)\s*[—–-]\s*(\d+)\s+"
                      + re.escape(away), text)
    if not score:
        raise ValueError("Final score/team order not found in rendered report")
    stats = re.search(r"STATS\s+(\d+)%\s+Possession\s+(\d+)%\s+"
                      r"(\d+)\s+Shots\s+(\d+)\s+(\d+)\s+Shots on target\s+(\d+)", text)
    if not stats:
        if not allow_missing_stats or re.search(r"\bSTATS\b", text):
            raise ValueError("Primary STATS table missing or malformed")
        values = [None] * 6
    else:
        values = list(map(int, stats.groups()))
        if not 99 <= values[0] + values[1] <= 101:
            raise ValueError("Possession values are inconsistent")
        if values[4] > values[2] or values[5] > values[3]:
            raise ValueError("Shots on target exceed shots")
    own = 0 if side == "home" else 1
    other = 1 - own
    goals = list(map(int, score.groups()))
    result = {
        "opponent": opponent, "side": side,
        "goalsFor": goals[own], "goalsAgainst": goals[other],
        "shotsFor": values[2 + own], "shotsAgainst": values[2 + other],
        "shotsOnTargetFor": values[4 + own],
        "shotsOnTargetAgainst": values[4 + other],
        "possessionPercent": values[own],
    }
    try:
        breakdown = text.split("HOW AGENTS PLAYED", 1)[1].split("AGENT PERFORMANCE", 1)[0]
        performance = text.split("AGENT PERFORMANCE", 1)[1]
    except IndexError as exc:
        raise ValueError("Agent tables missing") from exc

    def commands(name, following):
        head = re.search(re.escape(name) + r"\s+(\d+)\s+cmds\s*·\s*(\d+)\s*ms\s+avg", breakdown)
        if not head:
            raise ValueError("Command header missing for " + name)
        segment = breakdown[head.end():]
        if following:
            segment = segment.split(following, 1)[0]
        counts = {}
        for label, count, _percent in re.findall(r"([A-Za-z][A-Za-z ]*?)\s+(\d+)\s*·\s*(\d+)\s*%", segment):
            label = label.strip()
            if label not in ACTIONS:
                raise ValueError("Unrecognized rendered action: " + label)
            counts[ACTIONS[label]] = int(count)
        total, latency = map(int, head.groups())
        if sum(counts.values()) != total:
            raise ValueError("Command counts do not sum to reported total for " + name)
        return total, latency, counts

    count, latency, counts = commands(team, opponent if own == 0 else None)
    opponent_count, opponent_latency, _ = commands(opponent, team if own == 1 else None)
    result.update(commands=count, averageLatencyMs=latency,
                  commandCounts=counts, opponentCommands=opponent_count,
                  opponentAverageLatencyMs=opponent_latency)
    marker = team + " Position Latency Success "
    if marker not in performance:
        raise ValueError("Own agent performance table missing")
    segment = performance.split(marker, 1)[1]
    if own == 0:
        segment = segment.split(opponent, 1)[0]
    rows = re.findall(r"\b(GK|DEF|MID|FWD)\s+(\d+)\s*ms\s+(\d+)\s*%", segment)
    if [r[0] for r in rows] != ["GK", "DEF", "MID", "FWD", "FWD"]:
        raise ValueError("Expected five ordered role rows")
    roles = ["gk", "def", "mid", "fwd1", "fwd2"]
    result["roleLatencyMs"] = {role: int(row[1]) for role, row in zip(roles, rows)}
    success = {role: int(row[2]) for role, row in zip(roles, rows)}
    if len(set(success.values())) == 1:
        result["reportedRoleSuccessPercent"] = next(iter(success.values()))
    else:
        result["roleSuccessPercent"] = success
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--team", default="No Human in the Loop")
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--side", choices=["home", "away"], required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--setup", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-missing-stats", action="store_true",
                        help="Record absent primary STATS values as null after UI verification")
    args = parser.parse_args()
    data = {"id": args.id, "setup": args.setup,
            **parse_report(args.evidence.read_text(), args.team, args.opponent, args.side,
                           allow_missing_stats=args.allow_missing_stats)}
    data["limitations"] = [
        "Extracted from the rendered report; no inference/fallback mechanism is established.",
        "Reported Success and issued commands do not prove useful application of every action.",
        "Uncontrolled live opponent; one game does not establish a stronger policy.",
    ]
    if data["shotsFor"] is None:
        data["limitations"].append(
            "Primary STATS table absent in the rendered report; shots/on-target/possession are unknown (null), not zero.")
    output = json.dumps(data, indent=2) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
