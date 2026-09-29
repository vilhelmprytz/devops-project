import tomllib
from pathlib import Path


def load_config(path: Path = Path("config.toml")) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)
