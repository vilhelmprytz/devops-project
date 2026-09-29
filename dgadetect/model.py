"""Train, predict, save and load the DGA model."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import skops.io as sio
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression

BENIGN = "benign"


@dataclass
class Prediction:
    name: str
    malicious: bool
    family: str | None
    score: float


def train(
    names: list[str], labels: list[str], families: list[str], model_cfg: dict, seed: int
) -> dict:
    """One logistic regression per family, each trained on that family vs. benign."""
    # Stateless: nothing is fitted, so each family's classifier only depends on
    # benign data and that family's data.
    vectorizer = HashingVectorizer(
        analyzer="char",
        ngram_range=(1, model_cfg["ngram_max"]),
        n_features=model_cfg["n_features"],
        alternate_sign=False,
    )
    x = vectorizer.transform(names)
    y = np.array(labels)
    classifiers = {}
    for family in families:
        rows = (y == family) | (y == BENIGN)
        clf = LogisticRegression(
            C=model_cfg["C"], solver="liblinear", random_state=seed
        )
        clf.fit(x[rows], y[rows] == family)
        classifiers[family] = clf
    return {
        "vectorizer": vectorizer,
        "classifiers": classifiers,
        "decision_threshold": model_cfg["decision_threshold"],
    }


def predict(model: dict, names: list[str]) -> list[Prediction]:
    """The family whose classifier scores highest wins; malicious if score >= threshold."""
    x = model["vectorizer"].transform(names)
    families = list(model["classifiers"])
    scores = np.column_stack(
        [model["classifiers"][f].predict_proba(x)[:, 1] for f in families]
    )
    predictions = []
    for name, row in zip(names, scores, strict=True):
        best = int(row.argmax())
        score = float(row[best])
        malicious = score >= model["decision_threshold"]
        predictions.append(
            Prediction(name, malicious, families[best] if malicious else None, score)
        )
    return predictions


def save(model: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sio.dump(model, path)


def load(path: Path) -> dict:
    # No `trusted=` argument: skops then only loads its built-in safe types
    # (sklearn, numpy, scipy, builtins) and raises on anything else.
    return sio.load(path)
