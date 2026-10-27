# MID initial-position replay, 27 October 2026

Candidate, not installed or game-validated at authoring.

The existing L02B runtime passed its first initial-position request and one retry.
Subsequent readiness checks reused the same process and identical payload after
minutes of inactivity. Audit ordinals 3–10 then returned STALE_OR_DUPLICATE_FRAME.
The fresh cloud portal check was 4/5, MID failed with 0/1 active ticks. These are
observations, not evidence that the tactical passing policy failed in open play.

One correction: cache and replay only the previously validated non-sprinting
initial MOVE_TO when the complete state and session remain identical. Every
changed, invalid or progressed request invalidates that cache. No PASS/SHOOT is
cached; noninitial restarts, wrong identity, missing session and unknown geometry
retain their original guards. Repeating an identical positioning intent is
idempotent; this is not keyed to the Fitness caller or environment.

Rollback: retain the exact previous MID binding and code archive in private
receipts. Only MID may be changed. Preserve FWD4, DEF2, GK, FWD5 and formation.
Verify isolated runtime code/configuration, native repeated/changed/progressed
requests and full response timings; then fresh portal Fitness before any Practice.
An unchanged second Fitness check must also remain ready, not merely pass once.

The current Workshop Actions and Stats page, read 27 October 2026, states a
5-second maximum response time and about one invocation per two seconds. This
supersedes the older public 1-second rule for current event admission, not our
preference for fast responses. Report timings against both bounds; never discard
cold calls. Source: Workshop Studio, How to Play / Actions and Stats. No guarantee
of stronger football or completed passes follows from transport validation.

Local baseline: 81 MID tests passed; full suite had three existing M11 package
pin errors (fast-path dependency changed). A later Linux malformed-header test
hit ENOTCONN while half-closing after server rejection; the test helper now permits
only that errno and still requires the exact rejection response. No production
HTTP guard was weakened. Current native/Fitness/game outcomes will be recorded
only after execution.

## Native screening update, 17:56 UTC

The isolated V1 candidate returned 224/224 valid complete decisions in its broad
screen, but later targeted tests exposed two incomplete calls and a separate
fresh-session response of 5696.7 ms. It is withheld, not admitted by the earlier
passing subset. No portal binding or game has changed. See
[mid-replay-v1-screen.json](mid-replay-v1-screen.json).

Next bounded experiment keeps exactly the same code and switches only isolated
runtime platform V1 to V2. AWS documentation describes snapshot-based startup;
this is a latency hypothesis, not measured improvement yet. Source inspection
finds no startup credentials, random identifiers or external clients in this
stdlib handler. Startup-relative telemetry is not used to infer restored-instance
latency; full external response remains the measurement boundary.
Sources read: [platform versions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html)
and [V2 optimization](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-v2-optimize.html).

## Transport boundary correction and V2 qualification, 18:03 UTC

A dedicated instrumented call measured13120.7ms in the cloud client's proxy
CONNECT handshake, within15431.7ms total. This proves a client transport delay
in that trace, not that all previous cold-call latency has the same cause.
Initial V2 targeted and broad attempts retain their failed first calls.

A new explicitly qualified screen first cleaned up the earlier owned session
(already absent/terminated), establishing the SDK connection without invoking
or prewarming the agent. It then used six fresh runtime sessionIDs:224/224
valid complete responses, max2053.3ms; warm p95 232.1ms. All six owned probe
sessions stopped. No latency was subtracted from those224responses. This does
not measure new proxy connection setup or game-server timing, and does not
establish that V2 is universally faster than V1. See mid-replay-v2-screen.json.

Only MID was installed after this screen and exact configuration/archive
verification. First actual portal Fitness is running; no match has started.

Two unchanged portal Fitness checks completed5/5; exact five-role readback
confirms only MID changed. Prematch connectivity also passed (MID1065ms).
Practice01 then started, but the cloud Unity viewer failed with unsupported
WebGL before any pitch frame. The game remains running; visual observations
are unavailable, and commentary is not treated as physical action evidence.
Do not claim observed tactical improvements or start a second supposedly
observed game until the visual-observation limitation is resolved.
