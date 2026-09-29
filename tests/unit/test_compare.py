import json
import subprocess
import sys

from dgadetect.compare import check, to_markdown
from dgadetect.config import load_config

GATE = {"max_fpr": 0.01, "regression_tolerance": 0.005, "max_fnr": {"a": 0.2, "b": 0.5}}


def metrics(fpr: float, fnr_a: float, fnr_b: float) -> dict:
    return {"fpr": fpr, "families": {"a": {"fnr": fnr_a}, "b": {"fnr": fnr_b}}}


def failed(results: list[dict]) -> list[str]:
    return [r["metric"] for r in results if not r["ok"]]


def test_passes_within_limits():
    assert failed(check(metrics(0.005, 0.1, 0.4), None, GATE)) == []


def test_fails_over_absolute_limit():
    assert failed(check(metrics(0.02, 0.1, 0.6), None, GATE)) == ["fpr", "fnr b"]


def test_regression_within_tolerance_passes():
    baseline = metrics(0.001, 0.1, 0.4)
    assert failed(check(metrics(0.005, 0.104, 0.4), baseline, GATE)) == []


def test_regression_beyond_tolerance_fails():
    baseline = metrics(0.001, 0.1, 0.4)
    assert failed(check(metrics(0.007, 0.11, 0.4), baseline, GATE)) == ["fpr", "fnr a"]


def test_family_missing_from_baseline_gets_only_absolute_check():
    baseline = {"fpr": 0.005, "families": {"a": {"fnr": 0.1}}}
    assert failed(check(metrics(0.005, 0.1, 0.4), baseline, GATE)) == []


def test_family_without_a_limit_fails():
    with_extra_family = {
        "fpr": 0.005,
        "families": {"a": {"fnr": 0.1}, "b": {"fnr": 0.4}, "c": {"fnr": 0.0}},
    }
    assert failed(check(with_extra_family, None, GATE)) == ["fnr c"]


def test_family_missing_from_metrics_fails():
    missing_b = {"fpr": 0.005, "families": {"a": {"fnr": 0.1}}}
    results = check(missing_b, None, GATE)
    assert failed(results) == ["fnr b"]
    assert "| fnr b | - | - | 0.5000 | **FAIL** |" in to_markdown(results)


def test_real_config_catches_a_worse_fpr():
    gate = load_config()["gate"]
    families = {f: {"fnr": 0.1} for f in gate["max_fnr"]}
    baseline = {"fpr": 0.0061, "families": families}
    worse = {
        "fpr": 0.0099,
        "families": families,
    }  # still under max_fpr, but 60% more false positives
    assert failed(check(worse, baseline, gate)) == ["fpr"]


def run_cli(tmp_path, fpr: float) -> subprocess.CompletedProcess:
    families = {f: {"fnr": 0.0} for f in load_config()["gate"]["max_fnr"]}
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps({"fpr": fpr, "families": families}))
    return subprocess.run(
        [sys.executable, "-m", "dgadetect.compare", str(path)],
        capture_output=True,
        text=True,
    )


def test_cli_exit_codes(tmp_path):
    assert run_cli(tmp_path, 0.0).returncode == 0
    failing = run_cli(tmp_path, 1.0)
    assert failing.returncode == 1
    assert "**FAIL**" in failing.stdout
