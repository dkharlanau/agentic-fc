# 06 — Multi-round adversarial review / self-interview

This is a **documented design critique**, not a claim to expose private model reasoning. Each round asks hard questions and records a decision that can be tested.

## Round 1 — Rules lawyer vs football coach

**Q:** Can we choose press intensity just by looking at opponent possession?  
**A:** No. Position, closest eligible presser, defensive cover, stamina and side-of-field also matter. Rule: one designated primary presser, with explicit exception for immediate defensive danger.

**Q:** Does 31 SHOOT commands imply shooting too often?  
**A:** Not on its own: only six actual shots and zero on target in one report. Track executed actions and locations.

**Q:** No SHOOT commands, but four goals. Why?  
**A:** The game engine can act on CLEAR_OVERRIDE/maintained instructions; reports alone cannot attribute. Check raw tick events.

## Round 2 — Model engineer vs latency engineer

**Q:** Why not use Sonnet for every player?  
**A:** Intelligence has no value when the response misses deadline. Use same-state P95 latency and actual fitness results, not intuition.

**Q:** Are 1,400ms averages all failures if site says 1s?  
**A:** No: measurement scopes are unclear and the reports showed 100% success. Inspect trace boundaries/server timeouts before any claim.

**Q:** Could a tool-assisted agent be slower?  
**A:** Yes. LLM → Gateway → Lambda → LLM can exceed the per-tick budget. Compute deterministic heuristics locally when possible.

## Round 3 — Data-contract sceptic vs strategist

**Q:** Can agentId_3 alone identify the holder?  
**A:** No, IDs repeat across HOME/AWAY. Validate team indicator or unique hasBall flag, and represent ambiguous state.

**Q:** What if 'teamCode' is 'away' not 'AWAY'?  
**A:** Normalize case. Never hardcode HOME as default when missing.

**Q:** What if stamina field is 0.45 but we compare it to 40?  
**A:** That treats the player as always exhausted. Normalize physical runtime stamina and static skill stats separately.

## Round 4 — Opponent adaptation vs overfitting

**Q:** Why did we beat two opponents 4–0 but lose to a weak-command opponent?  
**A:** Opponent command volume is not a strength metric; game dynamics and built-in behaviour differ. Three games are too few.

**Q:** Should we force >=15 passes?  
**A:** No. Pass only when its expected value is higher than other actions.

**Q:** What if defensive compactness prevents all attack?  
**A:** Preserve asymmetric FWD support and increase controlled attacking risk late when behind.

## Round 5 — Reliability engineer vs tournament player

**Q:** Can LLM issue RESET to fix tactics?  
**A:** Not as default. RESET is team-wide; per-player agent must not unexpectedly override teammates.

**Q:** Does a successful fitness test prove no JSON issues?  
**A:** No. Repeat parsing tests under adversarial states; software serialization is safer.

**Q:** Should we delete the existing Harness when V2 is deployed?  
**A:** No. Keep A0 and only change portal mapping after controlled validation.

## Round 6 — Decision scientist vs model enthusiast

**Q:** Gateway labels a pass "0.82 success_probability" — is that real?  
**A:** No. The sample code uses arbitrary distance/interception heuristics; calibrate over observed matches before calling it probability.

**Q:** What's the marginal improvement worth testing first?  
**A:** Correct possession and team-side parsing, reliable serialization, and press coordination. Lower implementation risk and can affect every position.

**Q:** What outcome would disprove our favorite "compact counterpress" plan?  
**A:** Matched A/B games where it consistently creates fewer shots on target and worse goal difference with no compensating defensive benefit.

## Round 7 — Final architectural decision

**Decision:** retain Harness as a safety net, prototype a *fast deterministic controller*, add one model adviser only for ambiguous states within measured time budget, compare several opponents and both orientations. Do not call it tournament-optimized until results support the claim.
