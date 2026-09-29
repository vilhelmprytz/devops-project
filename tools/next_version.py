"""Print the next release version: the latest release bumped by the PR's label.

Usage: python tools/next_version.py LATEST_TAG "LABEL LABEL ..."
An empty LATEST_TAG means there is no release yet. Without a release:major or
release:minor label, the patch number is bumped.
"""

import sys


def next_version(latest: str | None, labels: list[str]) -> str:
    major, minor, patch = (int(p) for p in (latest or "v0.0.0").lstrip("v").split("."))
    if "release:major" in labels:
        return f"{major + 1}.0.0"
    if "release:minor" in labels:
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


if __name__ == "__main__":
    latest, labels = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""
    print(next_version(latest or None, labels.split()))
