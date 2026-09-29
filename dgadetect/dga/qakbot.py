"""Qakbot DGA.

Ported from Johannes Bader's reimplementation (GPL-2.0):
https://github.com/baderj/domain_generation_algorithms/blob/0faef452d267a62a94124ef2806bc4a72e0913bd/qakbot/dga.py
Only the command-line wrapper was removed; the algorithm is unchanged. Uses
upstream's defaults sandbox=False and seed=0.
"""

import binascii
from datetime import date

PERIOD_DAYS = 10
TLDS = ["com", "net", "org", "info", "biz", "org"]  # "org" twice, as upstream
MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def _seed(day: date, seed: int = 0) -> int:
    dx = (day.day - 1) // 10
    # upstream uses strftime("%b").lower(), which depends on the locale
    data = f"{min(dx, 2)}.{MONTHS[day.month - 1]}.{day.year}.{seed:08x}"
    return binascii.crc32(data.encode("ascii")) & 0xFFFFFFFF


def _int32(x: int) -> int:
    return 0xFFFFFFFF & x


class _MT19937:
    def __init__(self, seed: int):
        self.index = 624
        self.mt = [0] * 624
        self.mt[0] = seed
        for i in range(1, 624):
            self.mt[i] = _int32(
                1812433253 * (self.mt[i - 1] ^ self.mt[i - 1] >> 30) + i
            )

    def extract_number(self) -> int:
        if self.index >= 624:
            self.twist()
        y = self.mt[self.index]
        y = y ^ y >> 11
        y = y ^ y << 7 & 2636928640
        y = y ^ y << 15 & 4022730752
        y = y ^ y >> 18
        self.index = self.index + 1
        return _int32(y)

    def twist(self) -> None:
        for i in range(624):
            y = _int32(
                (self.mt[i] & 0x80000000) + (self.mt[(i + 1) % 624] & 0x7FFFFFFF)
            )
            self.mt[i] = self.mt[(i + 397) % 624] ^ y >> 1
            if y % 2 != 0:
                self.mt[i] = self.mt[i] ^ 0x9908B0DF
        self.index = 0

    def rand_int(self, lower: int, upper: int) -> int:
        r = self.extract_number() & 0xFFFFFFF
        return int(lower + float(r) / (2**28) * (upper - lower + 1))


def generate(day: date, count: int) -> list[str]:
    mt = _MT19937(_seed(day))
    domains = []
    for _ in range(count):
        tld = TLDS[mt.rand_int(0, len(TLDS) - 1)]
        length = mt.rand_int(8, 25)
        name = "".join(chr(mt.rand_int(0, 25) + ord("a")) for _ in range(length))
        domains.append(name + "." + tld)
    return domains
