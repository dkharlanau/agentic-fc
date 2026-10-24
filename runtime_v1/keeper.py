"""Conservative goalkeeper candidate; never routine pressure or wide pursuit."""
from agentic_fc.geometry import distance, line_distance, pass_score
from agentic_fc.policy import cmd, move


def keeper_options(state, movement_ready):
    me = state.my
    if state.side not in (0, 1) or me is None:
        return []
    if state.play_mode == 'KICK_OFF':
        # Native Fitness uses the documented logical frame. No guessed world
        # coordinate targets are emitted for the observed small-field profile.
        return [move(state, (-50 * state.sign, 0), 'GK_RESTART_LINE', False)] if movement_ready else []
    if state.play_mode != 'PLAY_ON':
        return []
    if state.i_have_ball:
        targets = []
        for mate in state.teammates:
            if mate.pid == 0:
                continue
            space = min((distance(o.x, o.y, mate.x, mate.y) for o in state.opponents), default=0)
            lane = min((line_distance(o.x, o.y, me.x, me.y, mate.x, mate.y)
                        for o in state.opponents), default=0)
            utility = pass_score(state, mate)
            if space >= 5.5 and lane >= 3 and utility >= .35:
                targets.append((utility, mate.pid))
        return [cmd(state, 'GK_DISTRIBUTE', {'target_player_id': pid, 'method': 'THROW'},
                    reason='GK_OPEN_OUTLET', score=utility)
                for utility, pid in sorted(targets, reverse=True)[:2]]
    # Only documented coordinates can support an explicit recovery target.
    # For the live proxy, CLEAR_OVERRIDE restores the engine goalkeeper.
    if movement_ready and distance(me.x, me.y, -50 * state.sign, 0) > 12:
        return [move(state, (-50 * state.sign, 0), 'GK_RECOVER_LINE', False)]
    return []
