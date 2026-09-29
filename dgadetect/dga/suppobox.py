"""Suppobox DGA.

Ported from Johannes Bader's reimplementation (GPL-2.0):
https://github.com/baderj/domain_generation_algorithms/blob/0faef452d267a62a94124ef2806bc4a72e0913bd/suppobox/dga.py
The word lists in wordlists/ are upstream's words1.txt to words3.txt. Only the
command-line wrapper was removed; the algorithm is unchanged. We use the
00:00 UTC time slot of each day and rotate through the three word lists by day.
"""

import calendar
from datetime import date
from functools import cache
from pathlib import Path

PERIOD_DAYS = 1
DOMAINS_PER_DAY = 85
SHUFFLE = [3, 9, 13, 6, 2, 4, 11, 7, 14, 1, 10, 5, 8, 12, 0]


@cache
def _words(word_list: int) -> list[str]:
    path = Path(__file__).parent / "wordlists" / f"suppobox{word_list}.txt"
    return [w.strip() for w in path.read_text().splitlines()]


def word_list_for(day: date) -> int:
    return day.toordinal() % 3 + 1


def generate(day: date, count: int) -> list[str]:
    words = _words(word_list_for(day))
    seed = calendar.timegm(day.timetuple()) >> 9
    domains = []
    for _ in range(min(count, DOMAINS_PER_DAY)):
        nr = seed
        res = 16 * [0]
        for i in range(15):
            res[SHUFFLE[i]] = nr % 2
            nr = nr >> 1

        first_word_index = 0
        for i in range(7):
            first_word_index <<= 1
            first_word_index ^= res[i]

        second_word_index = 0
        for i in range(7, 15):
            second_word_index <<= 1
            second_word_index ^= res[i]
        second_word_index += 0x80

        domains.append(words[first_word_index] + words[second_word_index] + ".net")
        seed += 1
    return domains
