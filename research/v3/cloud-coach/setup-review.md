# Setup review, 27 October 2026, 18:00 UTC

Read-only snapshot of the five portal bindings and their AWS configurations.
Private raw configuration receipts are retained; this report contains no resource
identifiers. Formation 1-1-2 and the original five bindings remain unchanged.

## Confirmed execution defect

MID source0028079 treats the third and subsequent identical initial state as
stale after consuming one retry. Repeated Fitness failed with zero active ticks.
The isolated replay correction is under qualification; no match evidence yet.

## Highest-priority risks, not established causes of losses

1. DEF's installed prompt says to pass and not dribble upfield, while the owner
   wants to preserve effective carrying unless a better safe pass exists. The
   prepared replacement addresses that tension but failed its AWAY native case.
   Do not install it without identifying the cause and mirrored regression tests.
2. DEF and FWD4 use model harnesses with maxIterations75 and timeoutSeconds3600,
   whereas the game allows5seconds per decision. These are configured ceilings,
   not proof that75iterations run or that each action takes an hour. Inspect real
   complete-response timing before attributing lag to these settings. Do not
   change FWD4, which the owner explicitly asked to preserve.
3. FWD4's installed prompt uses full-size coordinates and a25-unit shot range;
   previous recordings include a smaller coordinate frame. This is a risk of
   unit mismatch, not proof that any particular miss came from it. Inspect actual
   input and observed action together. Existing deterministic policies explicitly
   calibrate geometry; do not assume model prompts do the same.

Official Actions and Stats was read in all four tabs. PASS/SHOOT require
possession; PRESS_BALL above0.5 sprints; CLEAR_OVERRIDE returns to defaultAI;
RESET clears the entire team's overrides. The installed DEF/FWD4 prompts forbid
RESET. Zero reported portal latency is not a measured zero full response time.
Source: https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/6b-how-to-play/actions-and-stats

Next: restore repeatable Fitness first. Observe two unchanged Practice games,
including off-ball spacing and losing-possession transitions, before choosing
one tactical change. No claim of improved winning chances from this inspection.
