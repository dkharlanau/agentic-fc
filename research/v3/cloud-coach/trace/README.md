# Bounded match trace experiment

Owner request27October18:31UTC: add logs to understand game episodes despite the
cloud WebGL limitation. This is an observation change, not a tactical change.
The earlier cloud block closes at1/2 after the owner's diagnostic redirect; one
unobserved1:0win remains historical, not a completed comparative block.

Use one MID observer because it already receives all ten players and the ball.
MID_TRACE=1 enables a whitelisted snapshot after the complete response has been
flushed, outside the decision lock. Default is off. Maximum record8192bytes,
maximum10players. No team chat, player names, credentials, raw request, session
identifiers or arbitrary properties. Snapshots contain raw coordinates, declared
possession, energy, orientation and MID's intent. The other agents' intent is not
invented; follow-up state is observation, not proof of causation.

Keep raw logs and replay data private. Public code uses synthetic fixtures only.
A reconstruction must label raw coordinate frame, gaps and sampling interval;
never present it as footage from the game's blocked Unity viewer. Calibrate any
pitch overlay from verified input, not assumed dimensions. Missing possession
or identity is unknown. A submitted PASS is not a completed pass.

Checks: whitelist/privacy canaries, bounds/nonfinite values, input immutability,
response bytes unchanged and sent before even a blocked logger; complete unit
suite; reproducible archive and extracted HTTP replay. Then isolated V2 native
response/log verification and repeated Fitness before a new unchanged Practice
block. Existing source4de510a replay-safe MID is exact rollback. Do not change
DEF/FWD4/FWD5/GK, formation, passing or shooting policies in this experiment.
