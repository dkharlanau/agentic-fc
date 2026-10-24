# R1: bounded model selection Runtime pilot

Experimental FWD1 adapter and separate GK candidate. They are separate from the saved five-Harness team. Deployment and match outcomes belong in `research/v3`; local checks do not establish live strength. Exact experimental build/config recipes are in [profiles.json](profiles.json); original M8 remains the recovery reference.

The code unwraps the input, resolves HOME/AWAY and possession, computes a small legal action set, and asks Nova 2 Lite to choose an index. The model genuinely selects among actions: it can choose a shot or release control on the same state. Code owns player/team IDs, parameters, unlocked-command checks and JSON serialization. Model/API/format failures release only the assigned player's override. There is no rule-only fast path for valid invocations and no shell/browser/tool chain.

FWD1 routine support is delegated to built-in AI. Nearby shots and safe passes require explicit ownership or the separately labelled contact/motion inference described below. Pressure requires proximity, stamina and being the nearest outfield player. Contradictory or unresolved ownership cannot produce a shot/pass. This policy is a hypothesis to test, not a proven improvement.

## Live protocol findings

The first live Runtime trace exposed a mismatch with the synthetic Fitness examples: `OPEN_PLAY` and `unlockedCommands: []`. The initial adapter rejected every supported action before model selection. OPEN_PLAY now maps to PLAY_ON. An empty list is treated as no supplied restriction on basic commands; a nonempty list still filters options. The official sample does not enforce this field as a deny-all list. No RESET or tool commands become available.

The sanitized [observed AWAY fixture](../research/v3/fixtures/observed-live-away-open-play.json) has ball3D X/Y/Z, players2D X/Y, and keepers near X=-6/+6 rather than the documented -50/+50 examples. Ball X/Z velocity matches a nearby carrier's X/Y velocity in that snapshot. `sensing.py` detects this specific keeper/3D profile, uses ball X/Z as the ground plane, and pins an initial keeper-reference normalization per session. This is a coarse keeper-position proxy, not measured goalpost geometry or a validated command-coordinate conversion. Unresolved small-field3D inputs release control. Custom routine FWD movement remains delegated to the engine.

Duplicated agent IDs have no team discriminator or hasBall in the observed live state. A first-match lookup always favours the first team, while position alone can lag a turnover. The new optional inference requires a unique close contact, a distant same-ID competitor, and matching ball/player motion plus a carrier action, or consistent contact across distinct ticks. Explicit contradictory server fields prevent inference. It is logged as `contact_and_motion_inference`, never as server-confirmed ownership. Tests cover actual AWAY/mirrored HOME, contested contact, explicit false ownership, missing teams, and pinned/bounded references. These checks do not establish a live accuracy rate for the inference.

A bounded six-observation context is isolated by runtime session and passed to the model. Optional STM writes store the first and every tenth input/decision for private inspection; this is sampled evidence, not automatic cross-match training or weight updates. Raw events remain in the user's AWS account and must not enter Git. Static reviewed scouting is in [`tactical-memory.json`](../research/v3/tactical-memory.json).

The streaming entrypoint follows the [official AWS football sample](https://github.com/aws-samples/sample-ai-possibilities/blob/02fadb4bc7748eeb0d2ab6db150edfbd5766f63f/agentic-football-sample-agents/lib/agent_base.py), including explicit command `teamId`. The completed-JSON transport experiment (revision6) was rejected by portal Fitness with NO_PARSE despite five native probes passing. The portal explicitly requires the last SSE data line from `yield json.dumps(commands)`. Revision7 restores the exact v5 streaming code and decision policy. This does not establish that missing IDs caused earlier losses. The package uses the [AWS direct Python CodeZip path](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html): Python3.13, LinuxARM64 dependencies and `main.py` as entrypoint.

## Build and validate

```sh
python3 -m venv .local/r1-build-venv
.local/r1-build-venv/bin/pip install \
  --target .local/r1/dependencies \
  --platform manylinux2014_aarch64 --python-version 3.13 --only-binary=:all: \
  -r runtime_v1/requirements.lock.txt
python3 -m unittest tests.test_runtime_v1
python3 runtime_v1/build_package.py --dependencies .local/r1/dependencies
python3 runtime_v1/deploy.py
```

The builder checks dependency versions, ARM64 ELF headers, size and a source whitelist. It excludes caches, credentials, fixtures and private exports. `artifact.json` records source/archive hashes; binaries stay under `.local/`. Planning makes no AWS calls.

## Deploy after a workshop reset

Start with the [five-role recovery kit](../research/v3/recovery/README.ru.md). Use the new workshop's existing execution role and code bucket. Optionally create one three-day STM resource with no LTM strategies; supply its new ID below. The code does not create or modify IAM, bucket policies, encryption settings or endpoints.

Commit and push the exact built source before deployment. In an authorized AWS environment:

```sh
python3 runtime_v1/deploy.py \
  --archive .local/r1/deployment.zip \
  --bucket "$WORKSHOP_CODE_BUCKET" \
  --execution-role-arn "$NEW_WORKSHOP_EXECUTION_ROLE_ARN" \
  --memory-id "$NEW_STM_MEMORY_ID" \
  --receipt .local/r1/receipt.json \
  --apply
```

Omit `--memory-id` to disable sampled AWS writes. Credentials use the standard AWS chain. Deployment verifies that the selected Git commit contains the exact built source, preserves a private idempotency receipt, uploads into its content-addressed `nhitl-r1/` prefix, and creates/resumes one runtime. Retry the same command and receipt after an unknown outcome. It verifies saved role, artifact, environment, network and lifecycle fields when READY.

Before portal registration, invoke native HOME and AWAY possession probes and require valid own-team commands plus genuine accepted model choices, not just a release fallback. Stop only those own probe sessions. Then replace only FWD1 with the independent Runtime ARN, reload, require Fitness5/5, and play one live match. Preserve all original Harness ARNs privately for rollback. Review primary statistics and sampled events before expanding to more roles.

For an explicit revision of the same existing Runtime, preserve its prior receipt and pass `--update-from-receipt .local/r1/receipt.json --receipt .local/r1/revision2.json`. Build, commit and push the new source first. The helper verifies the existing name/role/region and saves a separate resumable update receipt; it does not replace the original record. Re-run native probes on the new receipt before registration.

`probe.py --receipt PRIVATE_READY_RECEIPT --output .local/r1/native-probes.json --apply` runs fresh synthetic HOME/AWAY sessions, reads returned commands and sampled audit events, and stops its own sessions in `finally`. Without `--apply` it only describes the plan. Sampled inputs and decisions use JSON text in conversational event fields: the initial blob-object trial was stored by this service as a map-style string, so it did not satisfy the structured audit gate.

The account-bound receipt, resource IDs, raw game inputs and access codes must stay private. A successful create or Fitness is not evidence of tactical improvement.

## Separate goalkeeper candidate

`--player-id 0 --name nhitl_gk_r2` creates a separate experimental goalkeeper Runtime; it must not replace the FWD1 Runtime. The same reviewed source archive can be used, but each role has an isolated environment, session and STM actor. Only0 and3 are accepted by the deployer; same-Runtime updates cannot change player identity. Its first native11/11 and portal Fitness5/5 gates passed; matched Practice is pending. These gates do not establish better shot prevention or saves.

GK code offers only safe distribution, documented-frame own-goal recovery/restart movement, and release to built-in goalkeeping. It never offers pressure, a shot, a normal pass or RESET. A receiver needs space and a clear lane; the marked nearest defender is excluded in the mirrored synthetic distribution fixtures. In the observed small-field profile, outgoing coordinate conversion remains unverified, so custom GK movement is unavailable. Native probes and portal Fitness are still required; no goalkeeper live improvement is claimed.

The standalone `tactics.py` observer remains excluded from the deployment source whitelist. Review hypotheses and critical rounds in [`adaptive-plan.ru.md`](../research/v3/adaptive-plan.ru.md).

## Output team scope experiment

Internal decisions retain the validated input team and assigned player. The optional `--wire-team-scope bound` deployment mode omits `teamId` from the serialized command, following the workshop prompt response schema and relying on the portal's registered-player binding. It does not invert numeric team IDs or permit commands for another player. Explicit output IDs remain the compatibility default until the field comparison is verified.

This tests an attribution/routing concern: several own R1 response counts and latencies resemble the opponent's reported forward. That could be report attribution, a wire-field mapping, or another client behavior. Native shape checks cannot establish the physical recipient. Require Fitness and matched Practice evidence; preserve the original Harness rollback. Audit records distinguish internal `selectedCommand`, actual `wireCommand` and `wireTeamScope`.

## Response readiness experiment

The outer async-generator path gives the SDK a stream before model work completes. A proposed revision instead awaits one decision and returns a precomputed normal generator. The SDK still emits the same SSE bytes; response readiness now follows the decision. The fake-client HTTP smoke requires completed model work before a response object is available and checks exact SSE bytes. This tests eager-header consumption by the game client; that client implementation is not accessible and the hypothesis remains unproven until native/Fitness/live checks. FWD1 prompt/options match v5 on the saved parity fixtures.

## Optional attack-support experiment

`--fwd-support-stance attack` offers FWD1 an engine `SET_STANCE` attack option when ownership is known, the player is off the ball, and no local pressure/interception action is offered. It avoids unverified world-coordinate movement. Restart, possession, stamina and command-unlock gates remain active. The default policy is unchanged. The selector prefers the offered support stance over release, but still makes a genuine bounded choice. Private audit retains the input previous command and both same-ID players last-actions to help distinguish report attribution from applied control. Native/Fitness and matched Practice evidence remain required; no improvement is claimed.

## Bounded coordinate diagnostic

`--fwd-coordinate-probe world-target` is an opt-in Practice diagnostic, disabled by default. Only FWD1 in the observed keeper-reference profile is offered a raw small `MOVE_TO` target `(4*attackSign,1.5)` without sprint during elapsed seconds8..28. The model is instructed to select the offered probe; a legal own release remains available on failure. It does not change team IDs or infer a movement conversion. Compare subsequent raw positions and same-ID last-actions before claiming raw or normalized output units. Native/Fitness gates alone cannot establish those units; diagnostic match outcomes must not enter policy-strength comparisons.

A second `--fwd-coordinate-probe own-wide` variant uses `(-2*attackSign,2.8)` in the same bounded window, to reduce ball-contact confounding. First field trace supports own-player control and raw units but is inconclusive because the carrier dribbled through the target region. Restore the working M8 portal bindings between diagnostics; an enabled probe is not a tournament policy.

## Measured movement and position-support candidate

Practice07 confirmed own HOMEplayer control and raw output units: consecutive movement directions align with the raw target at cosine>0.999999, while the normalized alternative fits worse. This does not survey goalposts or prove AWAY application. Agent command columns attributed own probes to the opponent and remain unreliable.

`--fwd-support-mode position` (alias `--fwd-support-stance`) offers FWD1 nonsprinting role targets only for known off-ball states, after local interception/pressure checks, when farther than4canonical units from the target. The model sees canonical options; selected movement is inversely transformed using the validated keeper-reference profile. Only the observed keeper-anchor range supports this conversion; unknown frames release to the engine. Raw-unit diagnostic and position modes are mutually exclusive. Other roles and model stay unchanged for the field comparison. Native9/Fitness and Practice are pending; no strength claim follows from43offline checks.
