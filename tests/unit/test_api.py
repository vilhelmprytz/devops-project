import pytest
from fastapi.testclient import TestClient

from dgadetect import api, model


@pytest.fixture
def client_for(tmp_path, monkeypatch):
    """Start the app with the given model saved as MODEL_PATH."""

    def make(trained: dict) -> TestClient:
        path = tmp_path / "model.skops"
        model.save(trained, path)
        monkeypatch.setenv("MODEL_PATH", str(path))
        return TestClient(api.app)

    return make


def test_predict_benign(client_for, tiny_model):
    with client_for(tiny_model) as client:
        response = client.get("/predict", params={"domain": "www.Google.com"})
    body = response.json()
    assert response.status_code == 200
    assert body["domain"] == "www.Google.com"
    assert body["name"] == "google"
    assert body["malicious"] is False
    assert body["family"] is None
    assert body["version"] == "dev"


def test_predict_dga(client_for, tiny_model):
    with client_for(tiny_model) as client:
        body = client.get("/predict", params={"domain": "qxzvkwbnjm.com"}).json()
    assert (body["malicious"], body["family"]) == (True, "consonants")


@pytest.mark.parametrize(
    "params", [{"domain": "co.uk"}, {"domain": "bücher.de"}, {"domain": "x" * 5000}, {}]
)
def test_predict_rejects_bad_input(client_for, tiny_model, params):
    with client_for(tiny_model) as client:
        assert client.get("/predict", params=params).status_code == 422


def test_version_comes_from_env(client_for, tiny_model, monkeypatch):
    monkeypatch.setenv("MODEL_VERSION", "1.2.3")
    with client_for(tiny_model) as client:
        assert (
            client.get("/predict", params={"domain": "google.com"}).json()["version"]
            == "1.2.3"
        )


def test_health_ok(client_for, tiny_model):
    with client_for(tiny_model) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "dev", "git_commit": "test"}


def test_health_fails_when_canary_is_flagged(client_for, tiny_model):
    flags_everything = {**tiny_model, "decision_threshold": 0.0}
    with client_for(flags_everything) as client:
        assert client.get("/health").status_code == 503


def test_app_does_not_start_without_a_model(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing.skops"))
    with pytest.raises(FileNotFoundError):
        with TestClient(api.app):
            pass
