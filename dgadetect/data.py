"""Build data/processed/{train,test}.csv from Tranco and the DGA generators."""

import csv
import hashlib
import math
import random
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from dgadetect.config import load_config
from dgadetect.dga import FAMILIES
from dgadetect.features import InvalidDomain, extract_name

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
TRANCO_URL = "https://tranco-list.eu/download/{list_id}/{size}"


def download_tranco(
    list_id: str, size: int, sha256: str, raw_dir: Path = RAW_DIR
) -> Path:
    path = raw_dir / f"tranco-{list_id}-{size}.csv"
    if not path.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(TRANCO_URL.format(list_id=list_id, size=size), path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != sha256:
        raise RuntimeError(f"{path}: sha256 is {actual}, config expects {sha256}")
    return path


def read_tranco(path: Path) -> list[str]:
    """Tranco CSV rows are 'rank,domain', best rank first."""
    with path.open(newline="") as f:
        return [domain for _rank, domain in csv.reader(f)]


def dga_domains(
    family: str, start: date, end: date, count: int, seed: int
) -> list[str]:
    """`count` distinct domains drawn from every period in [start, end].

    Asks each period for 25% extra, because some families repeat domains across
    periods (qakbot's seed only has 3 values per month), then samples `count`.
    """
    module = FAMILIES[family]
    days = [
        start + timedelta(days=d)
        for d in range(0, (end - start).days + 1, module.PERIOD_DAYS)
    ]
    per_day = math.ceil(1.25 * count / len(days))
    unique = list(
        dict.fromkeys(d for day in days for d in module.generate(day, per_day))
    )
    return random.Random(seed).sample(unique, min(count, len(unique)))


def build_rows(
    benign: list[str],
    dga: dict[str, dict[str, list[str]]],
    test_fraction: float,
    seed: int,
) -> list[dict]:
    """Turn domains into deduplicated rows with a name, label and split.

    `dga` maps family -> {"train": [...], "test": [...]}. Train comes before test,
    so a DGA name seen in train is dropped from test.
    """
    candidates = [(d, "benign", None) for d in benign]
    for family, splits in dga.items():
        candidates += [(d, family, "train") for d in splits["train"]]
        candidates += [(d, family, "test") for d in splits["test"]]

    rows = []
    seen = set()
    for domain, label, split in candidates:
        try:
            name = extract_name(domain)
        except InvalidDomain:
            continue
        if (label, name) in seen:
            continue
        seen.add((label, name))
        rows.append({"domain": domain, "name": name, "label": label, "split": split})

    labels_per_name = Counter(name for _label, name in seen)
    rows = [r for r in rows if labels_per_name[r["name"]] == 1]

    rng = random.Random(seed)
    for row in rows:
        if row["split"] is None:
            row["split"] = "test" if rng.random() < test_fraction else "train"
    return rows


def write_splits(rows: list[dict], out_dir: Path = PROCESSED_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for split in ("train", "test"):
        selected = sorted(
            (r for r in rows if r["split"] == split),
            key=lambda r: (r["label"], r["name"]),
        )
        with (out_dir / f"{split}.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["domain", "name", "label"], extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(selected)


def main() -> None:
    cfg = load_config()
    data = cfg["data"]
    tranco = data["tranco"]
    benign = read_tranco(
        download_tranco(tranco["list_id"], tranco["size"], tranco["sha256"])
    )
    dga = {
        family: {
            "train": dga_domains(
                family,
                *data["train_dates"],
                data["dga_train_count"],
                data["random_seed"],
            ),
            "test": dga_domains(
                family, *data["test_dates"], data["dga_test_count"], data["random_seed"]
            ),
        }
        for family in data["families"]
    }
    rows = build_rows(benign, dga, data["benign_test_fraction"], data["random_seed"])
    write_splits(rows)
    for (split, label), n in sorted(
        Counter((r["split"], r["label"]) for r in rows).items()
    ):
        print(f"{split:5} {label:9} {n}")


if __name__ == "__main__":
    main()
