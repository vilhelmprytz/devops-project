from datetime import date
from pathlib import Path

import pytest

from dgadetect.dga import FAMILIES

FIXTURES = Path(__file__).parent.parent / "fixtures" / "dga"


def upstream_domains(family: str) -> list[str]:
    """Fixture output of the upstream script; its first line is the command used."""
    lines = (FIXTURES / f"{family}.txt").read_text().splitlines()
    return [line for line in lines if not line.startswith("#")]


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_matches_upstream(family):
    expected = upstream_domains(family)
    assert FAMILIES[family].generate(date(2024, 3, 15), len(expected)) == expected
