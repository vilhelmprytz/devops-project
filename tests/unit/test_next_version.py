import subprocess
import sys

import pytest

from tools.next_version import next_version


@pytest.mark.parametrize(
    ("latest", "labels", "expected"),
    [
        (None, [], "0.0.1"),
        (None, ["release:minor"], "0.1.0"),
        ("v1.2.3", [], "1.2.4"),
        ("v1.2.3", ["documentation"], "1.2.4"),
        ("v1.2.3", ["release:minor"], "1.3.0"),
        ("v1.2.3", ["release:major"], "2.0.0"),
        ("v1.2.3", ["release:minor", "release:major"], "2.0.0"),
    ],
)
def test_next_version(latest, labels, expected):
    assert next_version(latest, labels) == expected


def test_cli_treats_empty_latest_as_no_release():
    out = subprocess.run(
        [sys.executable, "tools/next_version.py", "", "release:minor"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "0.1.0"


def test_cli_takes_labels_as_one_space_separated_argument():
    out = subprocess.run(
        [
            sys.executable,
            "tools/next_version.py",
            "v1.2.3",
            "documentation release:major",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "2.0.0"
