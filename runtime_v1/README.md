# R1: bounded model selection Runtime pilot

Experimental FWD1 adapter. It is separate from the saved five-Harness team. Deployment and match outcomes belong in `research/v3`; local checks do not establish live strength.

The code unwraps the input, resolves HOME/AWAY and possession, computes a small legal action set, and asks Nova 2 Lite to choose an index. The model genuinely selects among actions: it can choose a shot or release control on the same state. Code owns player/team IDs, parameters, unlocked-command checks and JSON serialization. Model/API/format failures release only the assigned player's override. There is no rule-only fast path for valid invocations and no shell/browser/tool chain.

FWD1 routine support is delegated to built-in AI. Confirmed nearby shots and safe passes remain available, while pressure requires proximity, stamina and being the nearest outfield player. Unknown or contradictory ownership cannot produce a shot/pass. This policy is a hypothesis to test, not a proven improvement.

A bounded six-observation context is isolated by runtime session and passed to the model. Optional STM writes store the first and every tenth input/decision for private inspection; this is sampled evidence, not automatic cross-match training or weight updates. Raw events remain in the user's AWS account and must not enter Git. Static reviewed scouting is in [`tactical-memory.json`](../research/v3/tactical-memory.json).

The streaming entrypoint follows the [official AWS football sample](https://github.com/aws-samples/sample-ai-possibilities/blob/02fadb4bc7748eeb0d2ab6db150edfbd5766f63f/agentic-football-sample-agents/lib/agent_base.py), including explicit command `teamId`. This does not establish that missing IDs caused earlier losses. The package uses the [AWS direct Python CodeZip path](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html): Python3.13, LinuxARM64 dependencies and `main.py` as entrypoint.

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
