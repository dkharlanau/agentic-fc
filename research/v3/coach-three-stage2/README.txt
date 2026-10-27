Owner-requested three-correction pilot, not promoted. Read plan.json and results.json.
Source00d9325, code in fast_path_v2/, DEF prompt here.24 focused tests pass.
GK/FWD2 native10/10; DEF2/3, AWAY expectedPASS returnedCLEAR. Initial DEF response
parser failed before text preservation; no pass claimed. All own native sessions stopped.
Owner cancelled two games and requested Dot handoff; zero matches with full package.

Deployment helpers are public; credentials, ARN bindings and receipts remain private
in .local/stage2-20261027. Run from repository root with configured AWS SDK Python.
deploy.py creates isolated resources or verifies matching receipts; does not register
portal roles. Never reuse receipt names for different code. native.py refuses overwrite
of existing native evidence; use a deliberate new output receipt for a new candidate.
Inspect saved receipt hashes/source before reuse. Fitness in portal is still mandatory.

Do not deploy DEF candidate before resolving/retesting AWAY behaviour. Do not infer
physical saves, pass completion or improved speed from these contract tests.
The successful FWD4/playerId3 stays untouched. Snapshot-owned account details must
never enter tracked files. See HANDOFF.md for final installed state and Fitness.
