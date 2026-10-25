# Coordinated role package R1

**Outcome: rejected before deployment.** Read [RESULT.md](RESULT.md) and
`outcome.json`. Three real-model revisions failed; latest2/26. The creation
script was not applied and original M8 remains registered. The protocol below
records the intended gates, not completed deployment or match steps.

Owner-authorized bundled experiment on 24 October 2026, following “сделай все за
раз как эксперимент” and the request for coordinated, informed decisions.
This supersedes the earlier offline-only mission for this bounded package.
It does not restart the historical eight-hour loop, heartbeat or power timer.

All five prompts change together. Formation remains 1-1-2; GK/DEF/MID/FWD1 remain
Nova 2 Lite, FWD2 Haiku 4.5. Memory, tools, execution role, limits and history are
unchanged. The original M8 prompts and resources are the exact rollback.
This estimates the package's usefulness, not each individual rule's effect.

## Mechanism and risks

- Replace the absolute 25-unit shot instruction with a conservative relative
  close/central/open opportunity gate. The two-keeper geometry fallback is a
  hypothesis; a moving keeper is not a goal post. The trial's 20%/10% thresholds
  are design choices, not estimated football physics or proven optimal cutoffs.
- Confirm possession using team plus player identity; cautiously resolve a
  duplicated owner ID by decisive proximity only. Ambiguity releases control.
- Choose open receivers and lanes, not automatically the closest player.
- One eligible presser; DEF keeps central cover; MID offers support; FWD1 links
  the attack; FWD2 provides depth. Short overrides limit stale pressing.
- No MOVE_TO: live observation-to-command coordinate mapping is not proven.
  Stances/default AI supply movement. Their actual shape is not guaranteed.

**A prompt is not an engine-level guard.** CLEAR_OVERRIDE can hand decisions to
built-in AI, including shooting. Thus these prompts cannot promise zero long
shots, zero turnovers or coordinated physical movement. A conservative shot gate
may starve attack; stances may be ignored; more prompt tokens may increase delay.
No trained weights or automatic cross-match learning are claimed.

## Gates and bounded protocol

1. Build prompts/portable bundle; run local contract tests. The baseline bundle
   remains byte-for-byte unchanged. Save hashes before model calls.
2. Evaluate all 21 counterfactual situations plus five stale-context cases with the actual assigned models via
   visible CloudShell. Expectations are never in the model request. Require
   26/26; failures block registration. These calls are not Harness/football tests.
3. Only after passing, clone five isolated Harness with the existing execution
   role. Read back every prompt/config and verify the originals still match M8.
4. Check no active game; register all five as one intended lineup. Registration
   is sequential, not atomic. Any incoming game during transition is excluded
   and labelled mixed/unknown, never counted as a coherent trial.
5. Require fresh Fitness 5/5. On a contract/identity/deployment failure, restore
   the original five and Fitness 5/5; do not begin the five-match cohort.
6. One stable block of five completed ranked games. No edits between ordinary
   wins/losses. Capture before/after leaderboard, HOME/AWAY, opponents, primary
   goals/shots/possession and timing. Keep incoming games separately reconciled.
7. Compare descriptively with stable M8 live63..72 (16 points/10, 12:11 goals;
   9/10 reports have shots). Different opponents/sides prevent a causal claim.
   Fewer than 8 points/5, a critical reliability failure, or repeated attack
   starvation rejects promotion. At least 8 points alone is not superiority:
   goal difference, zero-shot games, command reliability and opponent mix matter.
   Default after an inconclusive block is exact M8 rollback. Do not start another
   block without a new decision/authorization; no automatic background loop.

The previous 1-2-1 proposal is deferred. The frozen 80-report tournament audit is
not mutated; new results belong to this experiment's own journal.

## Reproduction

Local: `python3 research/v3/role-package-r1/build.py`, then
`python3 -m unittest discover -s research/v3/role-package-r1 -p 'test_*.py'`.

Visible AWS CloudShell only: `python3 research/v3/role-package-r1/evaluate.py --invoke --with-context`.
After actual model gates, `deploy.py --apply --source-bindings .local/.../bindings.json`
creates candidate resources and stores private receipts. No local AWS calls.
`deploy.py` without `--apply` is an offline plan. No credentials/ARNs in public Git.

For a fresh account the existing recovery bundle still restores M8 with
`research/v3/recovery/restore.py --profile baseline-m8`; full fresh-account
five-role recovery remains unverified. Restore instructions are separate from
any claim that this candidate passed the gates above.
