from datetime import date

import pytest

from dgadetect.data import build_rows, dga_domains, download_tranco


def test_build_rows_dedupes_by_name():
    benign = ["google.com", "google.de", "kth.se", "shared.com", "co.uk"]
    dga = {"necurs": {"train": ["aaa.ru", "shared.net"], "test": ["aaa.com", "bbb.ru"]}}
    rows = build_rows(benign, dga, test_fraction=0.5, seed=1)
    by_name = {r["name"]: r for r in rows}

    assert sorted(by_name) == [
        "aaa",
        "bbb",
        "google",
        "kth",
    ]  # "shared" had two labels, co.uk is invalid
    assert by_name["google"]["domain"] == "google.com"  # the best-ranked domain is kept
    assert (
        by_name["aaa"]["split"] == "train"
    )  # the test copy of a train name is dropped
    assert by_name["bbb"]["split"] == "test"
    assert {r["split"] for r in rows if r["label"] == "benign"} <= {"train", "test"}


def test_build_rows_is_deterministic():
    benign = [f"site{i}.com" for i in range(100)]
    assert build_rows(benign, {}, 0.2, seed=7) == build_rows(benign, {}, 0.2, seed=7)


def test_dga_domains_returns_distinct_domains():
    domains = dga_domains("qakbot", date(2025, 1, 1), date(2025, 3, 31), 500, seed=1)
    assert len(domains) == 500
    assert len(set(domains)) == 500


def test_download_tranco_rejects_wrong_checksum(tmp_path):
    (tmp_path / "tranco-TEST-10.csv").write_text("1,changed.com\n")
    with pytest.raises(RuntimeError, match="sha256"):
        download_tranco("TEST", 10, sha256="0" * 64, raw_dir=tmp_path)
