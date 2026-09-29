"""Necurs DGA.

Ported from Johannes Bader's reimplementation (GPL-2.0):
https://github.com/baderj/domain_generation_algorithms/blob/0faef452d267a62a94124ef2806bc4a72e0913bd/necurs/dga.py
Only the command-line wrapper was removed; the algorithm is unchanged.
"""

from datetime import date

PERIOD_DAYS = 4
MAGIC_NR = 9
DOMAINS_PER_DAY = 2048
TLDS = [
    "tj", "in", "jp", "tw", "ac", "cm", "la", "mn", "so", "sh", "sc", "nu", "nf", "mu",
    "ms", "mx", "ki", "im", "cx", "cc", "tv", "bz", "me", "eu", "de", "ru", "co", "su", "pw",
    "kz", "sx", "us", "ug", "ir", "to", "ga", "com", "net", "org", "biz", "xxx", "pro", "bit",
]  # fmt: skip


def _pseudo_random(value: int) -> int:
    loops = (value & 0x7F) + 21
    for index in range(loops):
        value += ((value * 7) ^ (value << 15)) + 8 * index - (value >> 5)
        value &= (1 << 64) - 1
    return value


def _domain(sequence_nr: int, day: date) -> str:
    n = _pseudo_random(day.year)
    n = _pseudo_random(n + day.month + 43690)
    n = _pseudo_random(n + (day.day >> 2))
    n = _pseudo_random(n + sequence_nr)
    n = _pseudo_random(n + MAGIC_NR)
    domain_length = n % 15 + 7

    domain = ""
    for i in range(domain_length):
        n = _pseudo_random(n + i)
        domain += chr(n % 25 + ord("a"))
        n += 0xABBEDF
        n = _pseudo_random(n)

    return domain + "." + TLDS[n % 43]


def generate(day: date, count: int) -> list[str]:
    return [_domain(i, day) for i in range(min(count, DOMAINS_PER_DAY))]
