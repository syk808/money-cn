# money-cn

Format amounts and large numbers in Chinese units (万 / 亿 / 万亿) instead of K / M / B.
One file, standard library only.

## The problem

Chinese readers count in units of 10^4 (万) and 10^8 (亿), not thousands and millions.
"$39M" has to be converted in the reader's head; "$3900万" does not. This module writes
numbers that way with one fixed rule, so every place that prints an amount prints it the
same way.

## Usage

Copy `money_cn.py` into your project.

```python
from money_cn import money_cn, count_cn, money_text_cn, count_text_cn, parse_usd_text

money_cn(1234567890)             # '$12.3亿'
money_cn(36360000)               # '$3636万'
money_cn(8901)                   # '$8,901'
money_cn(-3.2e8)                 # '-$3.20亿'
money_cn(3.2e8, sign=True)       # '+$3.20亿'
money_cn(1.2e9, unit="HK$")      # 'HK$12.0亿'
money_cn(20000, trim=True)       # '$2万'
money_cn(1234567, digits=0)      # '$123万'
money_cn(None)                   # '—'   (change with empty="")
count_cn(89000)                  # '8.90万'  (no currency sign)

money_text_cn("FDV $39M/$52M")   # 'FDV $3900万/$5200万'
count_text_cn("7.2M")            # '720万'
parse_usd_text("$ 150.0 mil")    # 150000000.0
parse_usd_text("12.3亿")         # 1230000000.0
parse_usd_text("TBA")            # None
```

## The rule

- `>= 1e4` is written in 万, `>= 1e8` in 亿, `>= 1e12` in 万亿.
- The number in front of the unit has two decimals below 10, one below 100, none
  otherwise. This is decided on the rounded number: 9.996 is written `10.0`.
- 9999.6万 carries over to `1.00亿` rather than `10000万`.
- Below 1e4: an integer with thousands separators (`$8,901`). Non-integers below 100
  keep two decimals (`$45.68`); values below 0.01 keep two significant digits.
- No space between the number and 万 / 亿.
- `trim=True` drops trailing zeros (`$2.00万` becomes `$2万`).
- Unreadable input (`None`, `""`, `"abc"`, NaN, infinity, booleans) returns `empty`.

Rounding reproduces JavaScript's `Number.prototype.toFixed`: the exact binary value of
the float is rounded, ties go up. A JavaScript implementation of the same rule
therefore prints the same text for the same number. Python's own `round()` and
`format()` use round-half-even and can differ in the last digit.

## Limits

- Not meant for prices, percentages or multiples.
- `money_text_cn` only rewrites `$` followed by a number and K / M / B / T (or `bn`,
  `million`, `billion`, `trillion`). Numbers without `$` (`552B`) and anything inside
  an `http(s)://` URL are left as they are. Other currency signs are not recognised.
- `count_text_cn` converts only when the whole string is a single K / M / B number.
- `parse_usd_text` returns `None` for negative numbers and for anything it cannot read
  in full; it does not try to pull a number out of a sentence.
- Input goes through `float`, so integers above 2^53 lose precision.
- The largest unit is 万亿; larger values are written as a big number of 万亿.

## 中文说明

把金额和大数写成「万 / 亿 / 万亿」，不用 K / M / B。≥1 万写「万」，≥1 亿写「亿」，
≥1 万亿写「万亿」；单位前的数小于 10 留两位小数、小于 100 留一位、其余取整；
不足 1 万写带千分位的整数；数字和单位之间不留空格。只依赖标准库，单文件，复制即可用。

## Tests

`unittest` only, no network, no third-party packages.

```
python -m unittest discover -s tests
```

## License

MIT
