# -*- coding: utf-8 -*-
"""Format amounts and large numbers in Chinese units (万 / 亿 / 万亿) instead of K / M / B.

Standard library only. The rule lives in this one file:

    money_cn(1234567890)            "$12.3亿"
    money_cn(36360000)              "$3636万"
    money_cn(8901)                  "$8,901"
    money_cn(-3.2e8)                "-$3.20亿"     (with sign=True positives get a "+")
    money_cn(89000, unit="")        "8.90万"       (counts without a currency sign; same as count_cn)
    money_cn(None)                  "—"            (change with empty="")

  >= 1e4 is written in 万, >= 1e8 in 亿, >= 1e12 in 万亿. The number in front of the unit
  gets two decimals below 10, one below 100, none otherwise (decided on the rounded number:
  9.996 is written 10.0). 9999.6万 carries over to 1.00亿. Below 1e4 the value is written
  as an integer with thousands separators. No space between the number and 万 / 亿.

Rounding reproduces JavaScript's Number.prototype.toFixed digit for digit (round the exact
binary value of the float, ties go up), so a JavaScript implementation of the same rule
prints the same text for the same number.

Three more helpers:
    money_text_cn("FDV $39M/$52M")  "FDV $3900万/$5200万"   rewrite $..K/M/B/T inside a text
    count_text_cn("89K")            "8.90万"                 the whole text is one K/M/B number without $
    parse_usd_text("$ 150.0 mil")   150000000.0              read an amount text as a number, None if unreadable
"""
from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

__all__ = ["money_cn", "count_cn", "money_text_cn", "count_text_cn", "parse_usd_text"]

_STEPS = ((1e4, "万"), (1e8, "亿"), (1e12, "万亿"))


def _to_fixed(x: float, places: int) -> str:
    """JavaScript's x.toFixed(places): round the exact binary value of x, ties go up. x >= 0."""
    return format(Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), "f")


def _fixed(x: float, digits) -> str:
    if isinstance(digits, int) and not isinstance(digits, bool):
        return _to_fixed(x, digits)
    text = _to_fixed(x, 2)
    if float(text) >= 10:
        text = _to_fixed(x, 1)
    if float(text) >= 100:
        text = _to_fixed(x, 0)
    return text


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if not value:
            return None
    try:
        v = float(value)
    except (TypeError, ValueError, InvalidOperation, OverflowError):
        return None
    return v if math.isfinite(v) else None


def _trim(body: str) -> str:
    """Drop trailing zeros after a decimal point, then a dangling decimal point: "2.00万" -> "2万"."""
    m = re.match(r"^([\d,]*\.\d*?)0+(\D*)$", body)
    if m:
        body = m.group(1) + m.group(2)
    return re.sub(r"[.](?=[^0-9]*$)", "", body)


def money_cn(value, unit: str = "$", sign: bool = False, digits=None, empty: str = "—", trim: bool = False) -> str:
    """A number -> "$12.3亿" / "$3636万" / "$8,901".

    value may be int / float / Decimal / numeric string; anything unreadable returns ``empty``.
    unit="" is for numbers that are not money (people, tokens, counts).
    digits fixes the number of decimals in front of 万 / 亿. trim=True drops trailing zeros.
    Not meant for prices, percentages or multiples.
    """
    v = _number(value)
    if v is None:
        return empty
    a = abs(v)
    unit = "$" if unit is None else str(unit)
    head = "-" if v < 0 else ("+" if sign and v > 0 else "")
    body = None
    if a < 1e4 and int(_to_fixed(a, 0)) < 1e4:
        if a >= 100 or a == math.floor(a) or float(_to_fixed(a, 2)) >= 100:
            body = "{:,}".format(int(_to_fixed(a, 0)))
        elif a >= 1 or (a >= 0.01 and unit):          # money goes to cents: $0.06, not $0.060
            body = _to_fixed(a, 2)
        else:
            body = _to_fixed(a, min(10, math.ceil(-math.log10(a)) + 1))
    else:
        for i, (step, name) in enumerate(_STEPS):
            text = _fixed(a / step, digits)
            if float(text) < 1e4 or i == len(_STEPS) - 1:      # 9999.6万 becomes 1.00亿, not 10000万
                body = text + name
                break
    if trim:
        body = _trim(body)
    return head + unit + body


def count_cn(value, sign: bool = False, digits=None, empty: str = "—", trim: bool = False) -> str:
    """A large number without a currency sign (people / tokens): 89000 -> "8.90万"."""
    return money_cn(value, unit="", sign=sign, digits=digits, empty=empty, trim=trim)


# -- $..K/M/B/T inside an existing text -> 万 / 亿 ---------------------------------------
# Only "$ + number + K/M/B/T (or bn / million / billion / trillion)" is recognised.
# Numbers without "$" such as 552B are not touched; neither is anything inside a URL.
_URL_RE = re.compile(r"https?://[^\s<>）)]+")
_MONEY_NUM = r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
_SP = "[  ]"            # a plain space or a no-break space
_MONEY_RE = re.compile(
    r"\$" + _SP + "?" + _MONEY_NUM + r"(?:"
    r"(?P<unit>[KkMmBbTt]|bn|BN|Bn)(?![A-Za-z0-9])"
    r"|" + _SP + r"(?P<sunit>[KkMmBbTt]|bn|BN|Bn|[Mm]illion|[Bb]illion|[Tt]rillion)(?![A-Za-z0-9\-'’])"
    r")"
)
_MONEY_MULT = {"k": 10 ** 3, "m": 10 ** 6, "b": 10 ** 9, "t": 10 ** 12, "bn": 10 ** 9,
               "million": 10 ** 6, "billion": 10 ** 9, "trillion": 10 ** 12}


def money_text_cn(text, trim: bool = False):
    """"FDV $39M/$52M" -> "FDV $3900万/$5200万". Non-strings and texts without a recognisable
    amount are returned unchanged."""
    if not isinstance(text, str) or "$" not in text:
        return text
    url_spans = [m.span() for m in _URL_RE.finditer(text)]

    def repl(m):
        if any(s <= m.start() < e for s, e in url_spans):
            return m.group(0)
        unit = (m.group("unit") or m.group("sunit") or "").lower()
        try:
            value = Decimal(m.group("num").replace(",", "")) * _MONEY_MULT[unit]
        except (InvalidOperation, KeyError, ArithmeticError):
            return m.group(0)
        return money_cn(value, empty="", trim=trim) or m.group(0)

    return _MONEY_RE.sub(repl, text)


_COUNT_TEXT_RE = re.compile(r"^\s*(?P<sign>[+\-−])?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?(?P<unit>[KkMmBb])\s*$")


def count_text_cn(text, trim: bool = False):
    """The whole text is one K/M/B number without "$" (people, shares):
    "89K" / "7.2M" / "-13K" -> "8.90万" / "720万" / "-1.30万".
    Texts containing "$" are handed to money_text_cn; everything else (percentages,
    numbers with words around them) is returned unchanged."""
    if not isinstance(text, str):
        return text
    m = _COUNT_TEXT_RE.match(text)
    if not m:
        return money_text_cn(text, trim=trim)
    try:
        value = Decimal(m.group("num").replace(",", "")) * _MONEY_MULT[m.group("unit").lower()]
    except (InvalidOperation, KeyError, ArithmeticError):
        return text
    sign = m.group("sign") or ""
    return ("-" if sign in ("-", "−") else sign) + count_cn(value, trim=trim)


# -- amount texts such as "$ 150.0 mil" -> number ----------------------------------------
_USD_TEXT_RE = re.compile(
    r"^\s*(?:US)?\$?\s*(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)\s*"
    r"(?P<unit>thousand|million|billion|trillion|mil|mln|mm|bil|bn|k|m|b|t|万亿|亿|万)?\.?\s*$",
    re.IGNORECASE)
_USD_TEXT_MULT = {"": 1, "k": 1e3, "thousand": 1e3, "m": 1e6, "mm": 1e6, "mil": 1e6, "mln": 1e6,
                  "million": 1e6, "b": 1e9, "bn": 1e9, "bil": 1e9, "billion": 1e9, "t": 1e12,
                  "trillion": 1e12, "万": 1e4, "亿": 1e8, "万亿": 1e12}


def parse_usd_text(text):
    """"$ 150.0 mil" -> 150000000.0; "$1.2B" -> 1200000000.0; numbers are returned as float.
    Returns None for anything unreadable (and for negative or non-finite numbers)."""
    if isinstance(text, bool) or text is None:
        return None
    if isinstance(text, (int, float, Decimal)):
        v = float(text)
        return v if math.isfinite(v) and v >= 0 else None
    m = _USD_TEXT_RE.match(str(text))
    if not m:
        return None
    try:
        return float(Decimal(m.group("num").replace(",", "")) * Decimal(str(_USD_TEXT_MULT[(m.group("unit") or "").lower()])))
    except (InvalidOperation, KeyError, ArithmeticError):
        return None
