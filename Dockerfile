FROM python:3.14-slim@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d AS requirements
RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv requirements --hash > requirements.txt

FROM python:3.14-slim@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d

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
