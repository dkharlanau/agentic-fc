"""Robust adapter for modern and older AFC game-state shapes."""
from __future__ import annotations
from dataclasses import dataclass, field
import json
import math
from typing import Any


@dataclass(frozen=True)
class Player:
    pid: int
    team: int
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    stamina: float = 1.0
    stats: dict[str, float] = field(default_factory=dict)
    has_ball: bool | None = None
    last_action: str = ""


@dataclass(frozen=True)
class State:
    side: int | None
    my_pid: int
    my: Player | None
    teammates: tuple[Player, ...]
    opponents: tuple[Player, ...]
    ball_x: float
    ball_y: float
    ball_vx: float
    ball_vy: float
    ball_status: str
    holder: tuple[int, int] | None
    game_time: float
    score_home: int
    score_away: int
    play_mode: str

    @property
    def sign(self) -> int:
        return 1 if self.side == 0 else -1

    @property
    def own_goal_x(self) -> float:
        return -55.0 * self.sign

    @property
    def opp_goal_x(self) -> float:
        return 55.0 * self.sign

    @property
    def progress(self) -> float:
        return self.sign * (self.my.x if self.my else 0)

    @property
    def our_goals(self) -> int:
        return self.score_home if self.side == 0 else self.score_away

    @property
    def their_goals(self) -> int:
        return self.score_away if self.side == 0 else self.score_home

    @property
    def we_have_ball(self) -> bool:
        return self.ball_status == "OURS"

    @property
    def i_have_ball(self) -> bool:
        return self.holder == (self.side, self.my_pid) and self.ball_status == "OURS"


def numeric(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        x = float(value)
        return x if math.isfinite(x) else default
    except (ValueError, TypeError):
        return default


def team_from(value: Any) -> int | None:
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("home", "0"):
            return 0
        if v in ("away", "1"):
            return 1
        return None
    return value if type(value) is int and value in (0, 1) else None


def player_id(row: dict) -> int | None:
    if "agentId" in row and isinstance(row["agentId"], str):
        try:
            n = int(row["agentId"].rsplit("_", 1)[-1])
            return n if 0 <= n <= 4 else None
        except (ValueError, IndexError):
            return None
    n = row.get("playerId")
    return n if type(n) is int and 0 <= n <= 4 else None


def normalize_stamina(value: Any) -> float:
    x = numeric(value, 1.0)
    if x > 1.0:
        x /= 100.0
    return min(1.0, max(0.0, x))


def parse_payload(payload: dict | str, my_pid: int) -> State:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError):
            payload = {}
    if not isinstance(payload, dict):
        payload = {}
    # Official Runtime sample nests serialized input as payload["prompt"].
    inner = payload.get("prompt")
    if inner is not None and "gameState" not in payload:
        if isinstance(inner, str):
            try:
                inner = json.loads(inner)
            except (ValueError, TypeError):
                inner = {}
        if isinstance(inner, dict):
            payload = inner

    gs = payload.get("gameState", payload)
    if not isinstance(gs, dict):
        gs = {}
    side = team_from(payload.get("teamId"))
    if side is None:
        side = team_from(payload.get("teamCode"))
    raw_players = gs.get("players", [])
    players = []
    if not isinstance(raw_players, list):
        raw_players = []
    for row in raw_players:
        if not isinstance(row, dict):
            continue
        pid = player_id(row)
        team = team_from(row.get("teamCode"))
        if team is None:
            team = team_from(row.get("teamId"))
        if pid is None or team is None:
            continue
        position = row.get("position") or {}
        velocity = row.get("velocity") or {}
        if not isinstance(position, dict) or not isinstance(velocity, dict):
            continue
        stats = row.get("stats") or {}
        skills = {}
        if isinstance(stats, dict):
            for k, v in stats.items():
                if isinstance(k, str):
                    skills[k.lower()] = numeric(v, 50.0)
        hb = row.get("hasBall")
        players.append(Player(
            pid=pid, team=team, x=numeric(position.get("x")),
            y=numeric(position.get("y")), vx=numeric(velocity.get("x")),
            vy=numeric(velocity.get("y")), stamina=normalize_stamina(row.get("stamina", 1.0)),
            stats=skills, has_ball=hb if isinstance(hb, bool) else None,
            last_action=str(row.get("lastAction") or "")
        ))
    own = tuple(sorted((p for p in players if p.team == side), key=lambda p: p.pid))
    opponents = tuple(sorted((p for p in players if p.team != side), key=lambda p: p.pid))
    matches = [p for p in own if p.pid == my_pid]
    me = matches[0] if len(matches) == 1 else None
    ball = gs.get("ball") or {}
    if not isinstance(ball, dict):
        ball = {}
    bp = ball.get("position") or {}
    bv = ball.get("velocity") or {}
    if not isinstance(bp, dict): bp = {}
    if not isinstance(bv, dict): bv = {}
    status, holder = resolve_possession(ball, players, side)
    score = gs.get("score") or {}
    if not isinstance(score, dict): score = {}
    return State(
        side=side, my_pid=my_pid, my=me, teammates=own, opponents=opponents,
        ball_x=numeric(bp.get("x")), ball_y=numeric(bp.get("y")),
        ball_vx=numeric(bv.get("x")), ball_vy=numeric(bv.get("y")),
        ball_status=status, holder=holder,
        game_time=numeric(gs.get("gameTime")),
        score_home=int(numeric(score.get("home"))),
        score_away=int(numeric(score.get("away"))),
        play_mode=str(gs.get("playMode") or "UNKNOWN"),
    )


def resolve_possession(ball: dict, players: list[Player], our_side: int | None) -> tuple[str, tuple[int, int] | None]:
    """Never infer a specific team from a duplicated agentId_N alone."""
    direct_holders = [p for p in players if p.has_ball is True]
    is_free = ball.get("isFree")
    if is_free is True:
        return ("UNKNOWN", None) if direct_holders else ("FREE", None)
    if len(direct_holders) > 1:
        return "UNKNOWN", None

    raw_id = ball.get("possessionAgentId")
    if isinstance(raw_id, str):
        try:
            pid = int(raw_id.rsplit("_", 1)[-1])
        except (ValueError, IndexError):
            return "UNKNOWN", None
    else:
        pid = ball.get("possessionPlayerId")
    if type(pid) is not int or not (0 <= pid <= 4):
        if len(direct_holders) == 1:
            h = direct_holders[0]
            owner = (h.team, h.pid)
            return ("OURS" if h.team == our_side else "THEIRS"), owner
        return ("FREE", None) if is_free is True else ("UNKNOWN", None)

    explicit_team = team_from(ball.get("possessionTeamCode"))
    if explicit_team is None:
        explicit_team = team_from(ball.get("possessionTeamId"))
    candidates = [p for p in players if p.pid == pid and
                  (explicit_team is None or p.team == explicit_team)]
    if len(direct_holders) == 1:
        h = direct_holders[0]
        if h.pid == pid and (explicit_team is None or h.team == explicit_team):
            owner = (h.team, h.pid)
            return ("OURS" if h.team == our_side else "THEIRS"), owner
        return "UNKNOWN", None
    if len(candidates) != 1:
        return "UNKNOWN", None
    h = candidates[0]
    owner = (h.team, h.pid)
    return ("OURS" if h.team == our_side else "THEIRS"), owner
