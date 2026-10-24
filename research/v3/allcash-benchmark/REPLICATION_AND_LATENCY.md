# Replication and bounded call-route diagnosis

24 October 2026. Same deployed8747a88/revision5, four M8 originals,1-1-2.

| Cohort07 opponent | Result | Shots | Side |
| --- | --- | --- | --- |
| Octopus | 3:1 | 8:2 | HOME |
| Octopus | 0:0, overtime | unavailable | HOME |
| Amber Geysers2 | 0:1, overtime | 11:2 | HOME |

1W1D1L,3:2goals,+4points. Account101→104games,173→177points,
134:92→137:94goals reconcile exactly; rank16→17. The current setup's six-game
total is4W1D1L,13:2goals,+13points. All HOME; two games scoreless, different
opponents uncontrolled. Do not conclude superiority from the earlier three wins.
The draw report contains no STATS section; unknown shot counts stay null.

Exact own fast FWD2 audit:284responses,0geometry failures,0modelcalls,
0SHOOT,66unknown-possession releases;13PASS,162STANCE. CPU medians
0.403/0.553/0.416ms. This does not prove those actions caused the game outcome.

## Where time was measured

Between blocks, with portalREADY and unchanged configuration, separate unique
probe sessions were used. These are CloudShell-path measurements, not game-server
latency or same-input model comparisons with an opponent.

| Path | First call | Warm complete | Additional evidence |
| --- | --- | --- | --- |
| Original GK, native InvokeHarness | 2389.9ms | 1039.5ms | model metrics897/644ms; warm headers331.3ms |
| Fast FWD2, InvokeAgentRuntime | 2910.0ms | 101.6/109.2/104.7ms | warm body reading0.17/0.29/0.28ms |

Fast warm median104.66ms. Almost all observed delay precedes response headers;
faster local computation or body decoding cannot remove the measured difference.
The remaining boundary includes service/routing/framework/network work; these
measurements do not isolate their shares. Fresh-session latency is much larger.

The GK's second input reused a session: input tokens2090→3373, output46both.
It returned fenced JSON. This does not establish how the portal parser handles
the response or whether that native session matches the game's input contract.

Both successful probe sessions were stopped with HTTP200. The first Harness
cleanup incorrectly used its internal managed RuntimeARN; AWS rejected it. The
unique probe session was recovered from exact prefixed logs and stopped through
the HarnessARN. The helper now saves its private session receipt before invoking.
No match session was stopped.

One compatibility check used the same original HarnessARN with InvokeAgentRuntime
and the prompt envelope used by our custom Runtime. AWS returned
ResourceNotFoundException before a response. Cleanup confirmed the session was
absent. This demonstrates the two API routes are not interchangeable for this
resource. It **does not establish which path the game server uses**.

## Decision and remaining work

The10ms full-path goal remains unmet. The repeated report profile of four tiny
latencies and one~80ms forward under different opponent names, original Harness
zero-invocation counters, exact own Runtime audits, and native API differences
justify continued attribution work. They do not prove opponent models, automatic
team inversion, or a platform routing defect. No new model is selected from these
tables. Do not change SSE to plainJSON: an earlier field attempt failedNO_PARSE.

Retain current candidate provisionally. The next tactical candidate must address
the two scoreless games with one bounded change and native/Fitness/Practice gates;
the earliest cheap discriminator is physical FWD2 support/action attribution.
Keep ownership safety and original FWD2v14 rollback. The renewed goal remains
active within its saved deadline; no claim of a completed winning setup.

Sources: [cohort07](../ranked-batch-07.json), [exact-session summaries](replication-audits.json),
[GK native](gk-route.json), [fast native](fast-route.json),
[compatibility failure](gk-runtime-envelope.json). Probe source is alongside these
results. Private receipts/raw states remain excluded from Git.

Recovery: [portable fast package recipe](../../../fast_path_v2/RECOVERY.ru.md),
manifest and source hashes are saved. The rebuilt archive passed CRC/SHA and all
nine deployed source files match8747a88. A new-workshop deployment remains untested.
