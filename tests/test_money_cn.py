# -*- coding: utf-8 -*-
"""Tests for money_cn: fixed expectations written from the rule, rounding, text helpers, trim."""
import os
import sys
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import money_cn  # noqa: E402
from money_cn import count_cn, money_text_cn, parse_usd_text  # noqa: E402

# (value, options, expected)
FIXED = [
    (1234567890, {}, "$12.3亿"),
    (822000000, {}, "$8.22亿"),
    (33310000000, {}, "$333亿"),
    (130510000000, {}, "$1305亿"),
    (1.26e12, {}, "$1.26万亿"),
    (45300, {}, "$4.53万"),
    (5040000, {}, "$504万"),
    (36360000, {}, "$3636万"),
    (453000, {}, "$45.3万"),
    (8901, {}, "$8,901"),
    (8901.6, {}, "$8,902"),
    (45.678, {}, "$45.68"),
    (0, {}, "$0"),
    (0.5, {}, "$0.50"),
    (-320000000, {}, "-$3.20亿"),
    (320000000, {"sign": True}, "+$3.20亿"),
    (2250000000, {"unit": ""}, "22.5亿"),
    (1200000000, {"unit": "HK$"}, "HK$12.0亿"),
    (1234567, {"digits": 0}, "$123万"),
    (999600000, {}, "$10.0亿"),
    (9996000000, {}, "$100亿"),
    (99960, {}, "$10.0万"),
    (999500, {}, "$100万"),
    (99999, {"unit": ""}, "10.0万"),
    (99.996, {}, "$100"),
    (9.996, {}, "$10.00"),
    (0.06, {}, "$0.06"),
    (0.02, {}, "$0.02"),
    (0.004, {}, "$0.0040"),
    (0.06, {"unit": ""}, "0.060"),
    (0.000776, {"unit": ""}, "0.00078"),
    (99996000, {}, "$1.00亿"),
    (9999.6, {}, "$1.00万"),
    (999960000000, {}, "$1.00万亿"),
    ("77000000", {}, "$7700万"),
    ("1,234,567", {}, "$123万"),
    (Decimal("16900"), {}, "$1.69万"),
    (None, {}, "—"),
    ("", {}, "—"),
    ("abc", {}, "—"),
    (None, {"empty": ""}, ""),
    (float("nan"), {}, "—"),
    (float("inf"), {}, "—"),
    (True, {}, "—"),
    (5e9, {}, "$50.0亿"),
    (10000, {}, "$1.00万"),
    (20000, {}, "$2.00万"),
    (1000, {}, "$1,000"),
    (4400000, {}, "$440万"),
    (16264000, {}, "$1626万"),
    (89000, {"unit": ""}, "8.90万"),
    (162000, {"unit": ""}, "16.2万"),
    (29000, {"unit": ""}, "2.90万"),
    (1092000, {"unit": ""}, "109万"),
    (38890000, {"unit": ""}, "3889万"),
    (2.2e11, {"unit": ""}, "2200亿"),
]


class FixedCasesTests(unittest.TestCase):
    def test_written_as_the_rule_says(self):
        for value, opts, want in FIXED:
            with self.subTest(value=value, opts=opts):
                self.assertEqual(money_cn.money_cn(value, **opts), want)

    def test_no_space_and_no_kmb(self):
        for value, opts, _ in FIXED:
            text = money_cn.money_cn(value, **opts)
            self.assertNotIn(" ", text)
            self.assertNotRegex(text, r"\d[KMBT]\b")

    def test_count_is_money_without_the_dollar(self):
        self.assertEqual(count_cn(89000), "8.90万")
        self.assertEqual(count_cn(-250000, sign=True), "-25.0万")
        self.assertEqual(count_cn(29000, sign=True), "+2.90万")
        self.assertEqual(count_cn(None, empty=""), "")

    def test_module_uses_the_standard_library_only(self):
        with open(os.path.join(ROOT, "money_cn.py"), encoding="utf-8") as fh:
            src = fh.read()
        imports = [l.strip() for l in src.split("\n") if l.startswith(("import ", "from "))]
        self.assertEqual(sorted(imports), ["from __future__ import annotations",
                                           "from decimal import ROUND_HALF_UP, Decimal, InvalidOperation",
                                           "import math", "import re"])


class RoundingTests(unittest.TestCase):
    """_to_fixed rounds the exact binary value of the float with ties going up,
    which is what JavaScript's Number.prototype.toFixed does."""

    def test_known_to_fixed_results(self):
        for x, places, want in [(1.005, 2, "1.00"), (8.345, 2, "8.35"), (1.45, 1, "1.4"),
                                (0.125, 2, "0.13"), (2.5, 0, "3"), (0.5, 0, "1"), (1.5, 0, "2"),
                                (0, 2, "0.00"), (1e21 / 1e12, 0, "1000000000")]:
            with self.subTest(x=x, places=places):
                self.assertEqual(money_cn._to_fixed(x, places), want)

    def test_exact_halves_carry_up(self):
        self.assertEqual(money_cn.money_cn(0.125), "$0.13")
        self.assertEqual(money_cn.money_cn(9999.5), "$1.00万")
        self.assertEqual(money_cn.money_cn(9999.4), "$9,999")
        self.assertEqual(money_cn.money_cn(99995000), "$1.00亿")
        self.assertEqual(money_cn.money_cn(99994999), "$9999万")


class TextToolsTests(unittest.TestCase):
    def test_parse_usd_text(self):
        for raw, want in [("$ 150.0 mil", 150_000_000.0), ("$150.0 mil", 150_000_000.0), ("$ 1.2 bil", 1.2e9),
                          ("$1.2B", 1.2e9), ("$ 75 mil", 75e6), ("$950K", 950_000.0), ("$1,234,567", 1234567.0),
                          ("US$8M", 8e6), ("150 million", 150e6), ("$ 0.5 mil.", 500_000.0), ("$3636万", 36_360_000.0),
                          ("12.3亿", 1.23e9), (150, 150.0), (1.5e8, 1.5e8), ("$ 1,150.5 mil", 1_150_500_000.0)]:
            with self.subTest(raw=raw):
                self.assertEqual(parse_usd_text(raw), want)

    def test_parse_usd_text_gives_none_when_it_cannot_read(self):
        for raw in (None, "", "-", "TBA", "N/A", "$", "mil", "$ 150 shares", "150 mil USD approx", True,
                    float("nan"), -5, "$-5 mil", "1.2.3 mil"):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_usd_text(raw))

    def test_money_text_cn(self):
        for raw, want in [("累计 $5B+", "累计 $50.0亿+"), ("$5B+", "$50.0亿+"),
                          ("流动性不足 $1k,价格可能失真", "流动性不足 $1,000,价格可能失真"),
                          ("FDV $39M/$52M", "FDV $3900万/$5200万"), ("≥$10K", "≥$1.00万"),
                          ("raised $1.5 billion in total", "raised $15.0亿 in total"),
                          ("see https://example.com/a?cap=$5M for $5M", "see https://example.com/a?cap=$5M for $500万"),
                          ("552B", "552B"), ("$3900万", "$3900万"), ("", "")]:
            with self.subTest(raw=raw):
                self.assertEqual(money_text_cn(raw), want)
        self.assertIsNone(money_text_cn(None))
        self.assertEqual(money_text_cn(42), 42)

    def test_count_text_cn(self):
        for raw, want in [("89K", "8.90万"), ("162K", "16.2万"), ("29K", "2.90万"), ("-13K", "-1.30万"),
                          ("+250K", "+25.0万"), ("7.2M", "720万"), ("5K", "5,000"), ("218 K", "21.8万"),
                          ("$70B", "$700亿"), ("3.4%", "3.4%"), ("3.75%–4.00%", "3.75%–4.00%"),
                          ("环比0.4%、同比3.4%", "环比0.4%、同比3.4%"), ("8.90万", "8.90万"), ("", "")]:
            with self.subTest(raw=raw):
                self.assertEqual(money_cn.count_text_cn(raw), want)
        self.assertIsNone(money_cn.count_text_cn(None))


class TrimTests(unittest.TestCase):
    """trim=True drops trailing zeros: round thresholds and targets inside a sentence."""

    def test_trim(self):
        cases = [(20000, {}, "$2万"), (250000, {"unit": ""}, "25万"), (8e8, {}, "$8亿"), (89000, {"unit": ""}, "8.9万"),
                 (1.64e8, {}, "$1.64亿"), (5e9, {}, "$50亿"), (1e6, {}, "$100万"), (2.5, {}, "$2.5"), (8901, {}, "$8,901")]
        for value, kw, expected in cases:
            with self.subTest(value=value, kw=kw):
                self.assertEqual(money_cn.money_cn(value, trim=True, **kw), expected)

    def test_default_keeps_the_digits(self):
        self.assertEqual(money_cn.money_cn(20000), "$2.00万")
        self.assertEqual(money_cn.count_cn(89000), "8.90万")

    def test_text_helpers_pass_trim_through(self):
        self.assertEqual(money_cn.money_text_cn("$5B+", trim=True), "$50亿+")
        self.assertEqual(money_cn.count_text_cn("89K", trim=True), "8.9万")
        self.assertEqual(money_cn.count_text_cn("3.4%", trim=True), "3.4%")


if __name__ == "__main__":
    unittest.main()
