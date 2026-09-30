import pytest

from dgadetect import model

BENIGN = [
    "google",
    "facebook",
    "wikipedia",
    "amazon",
    "netflix",
    "github",
    "youtube",
    "twitter",
    "reddit",
    "apple",
]
CONSONANTS = [
    "xkqzvbnmwq",
    "qzxvkjwpqz",
    "zzqxkvbwpq",
    "wqzkxjvbnm",
    "kxzqwvjbpq",
    "vqxzkwjbnp",
    "jqzxwkvbmp",
    "ysqdwkdpffwxnurw",  # the /health malicious canary
]
DIGITS = [
    "a1b2c3d4",
    "9z8y7x6w",
    "1q2w3e4r",
    "5t6y7u8i",
    "0o9i8u7y",
    "3e4r5t6y",
    "7u8i9o0p",
]
TINY_CONFIG = {
    "ngram_max": 3,
    "n_features": 2**12,
    "C": 10.0,
    "decision_threshold": 0.5,
}


@pytest.fixture(scope="session")
def tiny_model() -> dict:
    """A model trained in milliseconds on two made-up families."""
    names = BENIGN + CONSONANTS + DIGITS
    labels = (
        ["benign"] * len(BENIGN)
        + ["consonants"] * len(CONSONANTS)
        + ["digits"] * len(DIGITS)
    )
    trained = model.train(names, labels, ["consonants", "digits"], TINY_CONFIG, seed=0)
    trained["git_commit"] = "test"
    trained["trained_at"] = "2026-01-01T00:00:00+00:00"
    return trained
