"""Guard against inventing primary stats when a rendered draw omits them."""

import unittest

from report_parser import parse_report


def report(stats=""):
    return "1 text " + (
        "MATCH REPORT Own Team 0 — 0 Rival Draw "
        "AI OVERVIEW The narrator claims 99% possession and 90 shots. "
        + stats + " HOW AGENTS PLAYED Own Team 6 cmds · 1ms avg Clear 6 · 100 % "
        "Rival 7 cmds · 2ms avg Clear 6 · 86 % Pass 1 · 14 % "
        "AGENT PERFORMANCE Own Team Position Latency Success "
        "GK 2 ms 100 % DEF 2 ms 100 % MID 1 ms 100 % FWD 1 ms 100 % FWD 1 ms 100 % "
        "Rival Position Latency Success "
        "GK 3 ms 100 % DEF 3 ms 100 % MID 3 ms 100 % FWD 2 ms 100 % FWD 2 ms 100 %"
    )


class MissingStatsTest(unittest.TestCase):
    def test_missing_table_requires_explicit_opt_in(self):
        with self.assertRaises(ValueError):
            parse_report(report(), "Own Team", "Rival", "home")

    def test_opt_in_keeps_unknown_separate_from_zero_and_narrator_claims(self):
        result = parse_report(report(), "Own Team", "Rival", "home", allow_missing_stats=True)
        for key in ("shotsFor", "shotsAgainst", "shotsOnTargetFor",
                    "shotsOnTargetAgainst", "possessionPercent"):
            self.assertIsNone(result[key])
        self.assertEqual((result["goalsFor"], result["goalsAgainst"]), (0, 0))
        self.assertEqual(result["commands"], 6)
        self.assertEqual(result["commandCounts"], {"CLEAR_OVERRIDE": 6})

    def test_opt_in_does_not_hide_a_malformed_present_table(self):
        with self.assertRaises(ValueError):
            parse_report(report("STATS pending"), "Own Team", "Rival", "home",
                         allow_missing_stats=True)

    def test_existing_primary_table_takes_precedence_over_narrator(self):
        result = parse_report(report("STATS 42% Possession 58% 4 Shots 6 1 Shots on target 0"),
                              "Own Team", "Rival", "home", allow_missing_stats=True)
        self.assertEqual((result["shotsFor"], result["shotsAgainst"], result["possessionPercent"]),
                         (4, 6, 42))


if __name__ == "__main__":
    unittest.main()
