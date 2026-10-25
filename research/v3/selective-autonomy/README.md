# Selective intervention laboratory

Hypothesis: reduce forced striker movement by allowing built-in AI to handle routine support, while a model intervenes for clear shots, safe passes and nearby pressure.

`fwd1.txt` is rejected: HOME shot passed, AWAY returned an invalid empty command array. `fwd1-v2.txt` retains the full schema-clean baseline and appends a higher-priority policy; its first AWAY case returned a valid CLEAR_OVERRIDE but missed the intended SHOOT. Neither candidate was saved or played live. The baseline control on the same envelope returned a legal MOVE_TO, so category differences alone do not establish a parsing failure.

[Probe records](probes.json) preserve model, prompt hashes, tokens, latency and full-output contract evaluation. Each probe had a separate stopped session, with no active live game during testing. [Fixtures](fixtures.json) use mostly synthetic possession states; only the semantic kickoff envelope is grounded in an observed own native Fitness event. These are readiness heuristics, not evidence of match strength.
