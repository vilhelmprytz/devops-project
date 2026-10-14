FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS requirements
RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv requirements --hash > requirements.txt

FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170

WORKDIR /app
COPY --from=requirements /requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

COPY dgadetect/ dgadetect/
COPY artifacts/model.skops artifacts/model.skops

RUN useradd --create-home app
USER app

ARG MODEL_VERSION=dev
ENV MODEL_PATH=/app/artifacts/model.skops MODEL_VERSION=$MODEL_VERSION
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "dgadetect.api:app", "--host", "0.0.0.0", "--port", "8000"]
