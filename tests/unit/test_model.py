import pytest
import skops.io as sio
from skops.io.exceptions import UntrustedTypesFoundException

from dgadetect import model


def test_predict_picks_the_best_family(tiny_model):
    benign, consonants, digits = model.predict(
        tiny_model, ["google", "qxzvkwbnjm", "2k4j6h8g"]
    )
    assert (benign.malicious, benign.family) == (False, None)
    assert (consonants.malicious, consonants.family) == (True, "consonants")
    assert (digits.malicious, digits.family) == (True, "digits")


def test_threshold_decides_malicious(tiny_model):
    never = {**tiny_model, "decision_threshold": 1.01}
    always = {**tiny_model, "decision_threshold": 0.0}
    assert not model.predict(never, ["qxzvkwbnjm"])[0].malicious
    assert model.predict(always, ["google"])[0].malicious


def test_save_load_roundtrip(tiny_model, tmp_path):
    model.save(tiny_model, tmp_path / "model.skops")
    loaded = model.load(tmp_path / "model.skops")
    names = ["google", "qxzvkwbnjm"]
    assert model.predict(loaded, names) == model.predict(tiny_model, names)


class NotAllowed:
    pass


def test_load_refuses_unknown_types(tmp_path):
    sio.dump({"x": NotAllowed()}, tmp_path / "bad.skops")
    with pytest.raises(UntrustedTypesFoundException):
        model.load(tmp_path / "bad.skops")
