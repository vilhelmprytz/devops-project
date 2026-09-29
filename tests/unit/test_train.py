from dgadetect.train import evaluate


def test_evaluate(tiny_model):
    names = ["google", "amazon", "qxzvkwbnjm", "2k4j6h8g"]
    labels = [
        "benign",
        "benign",
        "consonants",
        "consonants",
    ]  # the digits one is attributed wrongly
    metrics = evaluate(tiny_model, names, labels, ["consonants"])
    assert metrics == {
        "fpr": 0.0,
        "families": {"consonants": {"fnr": 0.0, "attribution_accuracy": 0.5}},
    }
