# 01 — Evidence from supplied practice matches

Data: three result summaries supplied by the participant. This is a **small convenience sample**, not tournament-wide performance. Team was called **No Human in the Loop** in the summaries; earlier portal team name differed.

| Opponent | Result | Possession | Real shots | On target | Commands | Press | Intercept | Pass | Shoot | Average latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| The Benchmark FC | 4–0 W | 18% | 7 | 4 | 365 | 100 | 60 | 22 | 28 | 1281 ms |
| Total Attack United | 0–1 L | 46% | 6 | 0 | 335 | 100 | 43 | 8 | 31 | 940 ms |
| EL Real de AI | 4–0 W | 24% | 5 | 4 | 445 | 160 | 88 | 0 | 0 | 843 ms |

**Aggregate:** 2 wins, 1 loss, goals 8–1. No claim of statistical significance. Player success rate shown as 100% in all three reports despite one separate pre-match NO_PARSE episode that subsequently passed on retry.

## Interpretation and pitfalls

1. The team can score with modest possession. This supports exploring direct transitions; it does NOT establish that high press alone caused the goals.
2. 31 SHOOT *commands* in the loss created six real shots and zero on target. Counts of issued commands are not counts of executed actions. Track command validity, possession at issuance, timing, positions and shot outcome.
3. The 4–0 against EL Real de AI records four goals and **zero SHOOT commands**. Built-in engine actions are a plausible contributor. Validate in traces; don't decree that SHOOT commands are always necessary.
4. Opponent command-count comparisons are misleading: CLEAR_OVERRIDE returns player control to built-in AI. Low command counts do not mean still players.
5. The auto-generated match overview for Total Attack called 46% possession "dominated possession", which is internally inconsistent. Treat narrative explanations as leads, not forensic proof.
6. All five players' latency averages vary by match; these are not head-to-head model benchmarks under identical inputs.
7. There are conflicting latency limits in available materials (500 ms vs 1 s). The event site specifies **1 s**, but the current portal's measured deadline must prevail.

## What to inspect next (priority)

For MID, FWD1, FWD2, collect three **redacted** input-output cases each:
- possession claimed by own player / ambiguous agentId_N;
- ball free;
- possession on the other side;
- shot near goal with keeper and blockers visible;
- at least one AWAY case.

Look for **teamId**, **myPlayers**, **ball.isFree**, **ball.possessionAgentId**, possible **player.hasBall**, **teamCode**, **position**, **velocity**, **stamina**, **lastAction** and **stats**. Do not assume all fields are present in Harness prompts; capture first.

## Decision metrics

Primary: win rate by opponent class, goal difference, shots on target / real shots, goals conceded.
Quality: pass retention/turnovers where events exist, dangerous-zone turnovers, time to first recovery, player spacing, remaining stamina late game.
Reliability: JSON parse rate, legal command rate, applied command rate, timeout rate, P50/P95/P99 latency, fallback rate.
A/B guardrails: do not regress away-side or lose >5% of decision validity even if one score improves.

**Do not optimise for PASS or SHOOT counts.** They are diagnostic features only.
