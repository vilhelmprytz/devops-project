"""Pushdo DGA (the kz_v1 configuration).

Ported from Johannes Bader's reimplementation (GPL-2.0):
https://github.com/baderj/domain_generation_algorithms/blob/0faef452d267a62a94124ef2806bc4a72e0913bd/pushdo/dga.py
Only the command-line wrapper and the other configurations were removed; the
algorithm is unchanged. Upstream appends ".kz" whatever the configuration.
"""

import hashlib
import struct
from datetime import date

PERIOD_DAYS = 1
DOMAINS_PER_DAY = 30
CONSO_A = "bcdfghjklmnpqrstvwx"
CONSO_B = "zxtsrqpnmlkgfdc"
VOWELS_A = "aeiou"
VOWELS_B = "aio"
MOD = 7
MOD2 = 1


def _part(r: int) -> str:
    string = CONSO_A[r % len(CONSO_A)]
    rp2 = r + 2
    string += VOWELS_A[((r + 1) & 0xFF) % 5]
    if string[1] == "e" and rp2 & MOD:
        v = VOWELS_B[rp2 % 3]
    else:
        if not (rp2 & MOD2):
            return string
        v = CONSO_B[(r + 3) % 15]
    return string + v


def _domain(md5: bytes, length: int) -> str:
    domain = ""
    for i in range(16):
        domain += _part(md5[i])
        if len(domain) >= length:
            return domain[:length] + ".kz"
    raise AssertionError("unreachable: 16 parts are always long enough")


def _days_since_0(d: date) -> int:
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if not d.year % 4:
        days_in_month[1] = 29
    t = 0
    month = d.month - 1
    while month > 0:
        t += days_in_month[month]
        month -= 1
    return d.day + t + 365 * (d.year - d.year // 4) + 366 * (d.year // 4)


def generate(day: date, count: int) -> list[str]:
    r = _days_since_0(day)
    domains = []
    for _ in range(min(count, DOMAINS_PER_DAY)):
        md5 = hashlib.md5(struct.pack("<I", r), usedforsecurity=False).digest()
        r = struct.unpack("<I", md5[:4])[0]
        domains.append(_domain(md5, (r & 3) + 9))
        r += 1
    return domains
