"""HTTP API: GET /predict?domain=... and GET /health."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from dgadetect import model
from dgadetect.features import InvalidDomain, extract_name

CANARY = "google.com"  # a known-benign domain; /health fails if it is flagged


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = model.load(
        Path(os.environ.get("MODEL_PATH", "artifacts/model.skops"))
    )
    app.state.version = os.environ.get("MODEL_VERSION", "dev")
    yield


app = FastAPI(title="dgadetect", lifespan=lifespan)


@app.get("/predict")
def predict(domain: str, request: Request) -> dict:
    try:
        name = extract_name(domain)
    except InvalidDomain as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    p = model.predict(request.app.state.model, [name])[0]
    return {
        "domain": domain,
        "name": p.name,
        "malicious": p.malicious,
        "family": p.family,
        "score": round(p.score, 4),
        "version": request.app.state.version,
    }


@app.get("/health")
def health(request: Request) -> JSONResponse:
    state = request.app.state
    canary = model.predict(state.model, [extract_name(CANARY)])[0]
    body = {
        "status": "ok" if not canary.malicious else "canary flagged as malicious",
        "version": state.version,
        "git_commit": state.model["git_commit"],
    }
    return JSONResponse(body, status_code=200 if not canary.malicious else 503)
