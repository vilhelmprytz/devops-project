"""Checks on the built dataset. Run `make data` first; `make test-data` runs these."""

import csv
from pathlib import Path

import pytest

from dgadetect.config import load_config
from dgadetect.features import extract_name

PROCESSED = Path("data/processed")
DATA_CFG = load_config()["data"]


@pytest.fixture(scope="module")
def splits() -> dict[str, list[dict]]:
    result = {}
    for split in ("train", "test"):
        path = PROCESSED / f"{split}.csv"
        if not path.exists():
            pytest.fail(f"{path} is missing: run `make data` first")
        with path.open(newline="") as f:
            result[split] = list(csv.DictReader(f))
    return result


def test_labels_are_benign_plus_configured_families(splits):
    for rows in splits.values():
        assert {r["label"] for r in rows} == {"benign", *DATA_CFG["families"]}


def test_names_are_valid_and_match_domain(splits):
    for rows in splits.values():
        for r in rows:
            assert r["name"] == extract_name(r["domain"]), r


def test_every_name_appears_once(splits):
    """Covers duplicates within a label, names under two labels, and train/test leaks."""
    names = [r["name"] for rows in splits.values() for r in rows]
    assert len(names) == len(set(names))


@pytest.mark.parametrize(
    ("split", "key"), [("train", "dga_train_count"), ("test", "dga_test_count")]
)
def test_family_counts(splits, split, key):
    for family in DATA_CFG["families"]:
        count = sum(r["label"] == family for r in splits[split])
        assert count >= 0.9 * DATA_CFG[key], f"{family}/{split}: {count} rows"
