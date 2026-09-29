"""Train on data/processed/train.csv, evaluate on test.csv, write artifacts/."""

import csv
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from dgadetect import model
from dgadetect.config import load_config

PROCESSED_DIR = Path("data/processed")
ARTIFACTS_DIR = Path("artifacts")


def read_split(path: Path) -> tuple[list[str], list[str]]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["name"] for r in rows], [r["label"] for r in rows]


def evaluate(
    trained: dict, names: list[str], labels: list[str], families: list[str]
) -> dict:
    predictions = model.predict(trained, names)
    benign = [
        p for p, label in zip(predictions, labels, strict=True) if label == model.BENIGN
    ]
    metrics = {
        "fpr": round(sum(p.malicious for p in benign) / len(benign), 4),
        "families": {},
    }
    for family in families:
        preds = [
            p for p, label in zip(predictions, labels, strict=True) if label == family
        ]
        metrics["families"][family] = {
            "fnr": round(sum(not p.malicious for p in preds) / len(preds), 4),
            "attribution_accuracy": round(
                sum(p.family == family for p in preds) / len(preds), 4
            ),
        }
    return metrics


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        )
    except OSError:  # git is not installed
        return "unknown"
    return out.stdout.strip() if out.returncode == 0 else "unknown"


def main() -> None:
    cfg = load_config()
    families = cfg["data"]["families"]
    trained = model.train(
        *read_split(PROCESSED_DIR / "train.csv"),
        families,
        cfg["model"],
        cfg["data"]["random_seed"]
    )
    trained["git_commit"] = git_commit()
    trained["trained_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    metrics = evaluate(trained, *read_split(PROCESSED_DIR / "test.csv"), families)

    model.save(trained, ARTIFACTS_DIR / "model.skops")
    (ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
