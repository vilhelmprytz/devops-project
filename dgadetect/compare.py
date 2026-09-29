"""The metrics gate: compare metrics.json to the config limits and a baseline."""

import argparse
import json
import sys
from pathlib import Path

from dgadetect.config import load_config


def check(metrics: dict, baseline: dict | None, gate: dict) -> list[dict]:
    """One result per metric: {metric, baseline, new, limit, ok}.

    Every family in the gate or in the metrics is checked; a family with no limit
    or no metric fails, so a newly added family can't slip through unchecked.
    """
    tolerance = gate["regression_tolerance"]
    checks = [
        ("fpr", metrics["fpr"], gate["max_fpr"], baseline["fpr"] if baseline else None)
    ]
    for family in dict.fromkeys([*gate["max_fnr"], *metrics["families"]]):
        new = metrics["families"].get(family, {}).get("fnr")
        old = baseline["families"].get(family, {}).get("fnr") if baseline else None
        checks.append((f"fnr {family}", new, gate["max_fnr"].get(family), old))

    results = []
    for metric, new, limit, old in checks:
        ok = (
            new is not None
            and limit is not None
            and new <= limit
            and (old is None or new <= old + tolerance)
        )
        results.append(
            {"metric": metric, "baseline": old, "new": new, "limit": limit, "ok": ok}
        )
    return results


def _fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.4f}"


def to_markdown(results: list[dict]) -> str:
    lines = ["| Metric | Baseline | New | Limit | Result |", "|---|---|---|---|---|"]
    for r in results:
        result = "pass" if r["ok"] else "**FAIL**"
        lines.append(
            f"| {r['metric']} | {_fmt(r['baseline'])} | {_fmt(r['new'])} | {_fmt(r['limit'])} | {result} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()

    metrics = json.loads(args.metrics.read_text())
    baseline = json.loads(args.baseline.read_text()) if args.baseline else None
    results = check(metrics, baseline, load_config()["gate"])
    print(to_markdown(results))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
