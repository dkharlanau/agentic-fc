# 07 — Deployment decision and safe handoff

## Current state

The five existing Harness agents belong to the participant's event AWS account; they are independent from this GitHub repo. This project is **not deployed** and contains no ARN, team code, credentials or PII.

## Phase 1: Harness only

To try a prompt variant:
1. Copy active prompt to a private backup.
2. Paste the **complete** role-specific prompt in prompts/harness into corresponding Advanced Harness.
3. Keep assigned playerId identical: GK=0 DEF=1 MID=2 FWD1=3 FWD2=4.
4. Keep authorized 'Use another role → team-SolutionAccessRole-*'; disable optional Memory/Tools unless purposefully testing them.
5. Run Pre-match Fitness repeatedly, then controlled practice. Roll back if it regresses.
6. Save version and match ID. *Editing Harness instructions usually affects subsequent invocations without redeploy.*

**Warning:** this repo's prompts are proposed variants, not copies of the active, already-winning prompts.

## Phase 2: Python Runtime

1. Review official AWS sample Strands Runtime deployment instructions for the **current workshop account**.
2. Reuse official proven BedrockAgentCoreApp / entrypoint / stream shape and payload conventions.
3. Integrate agentic_fc.policy into official Runtime adapter; emit exactly one legal per-player command as JSON.
4. Validate that teamId is passed from payload, not hardcoded HOME.
5. Test normal responses plus simulated model timeouts, malformed model outputs and unknown possession.
6. Run local tests, then deploy to approved us-east-1 role. Account may not permit CDK bootstrap/IAM creation.
7. Run Fitness on **new Runtime ARNs**, test practice separately, then swap live portal mappings. Preserve Harness A0.

The code in this repo intentionally stops before a credential-dependent network deployment and before selecting a live Bedrock model.

## Gateway and Memory are optional

Official Gateway CDK implementation uses IAM, Lambda, CloudFormation, MCP and new roles. It may fail against the workshop participant role. A second legacy installer creates independent resources; **never run both**.

Memory could be useful for opponent tendencies but must be bounded and keyed by match session. Memory that carries across opponents may hurt. Baseline: no automatic memory provisioning.

## Before publishing a match trace

Remove team codes, AWS account IDs, harness/runtime ARNs, personal data, endpoint headers, credentials and any other event-only secrets. This is a **public** GitHub repository.

## Operational rollback

Original Harness remains active in AWS. If Runtime B shows NO_PARSE, excess latency, wrong team or excessive goals conceded, revert the Player Portal to the preserved A0 ARN mapping.
