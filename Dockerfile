FROM python:3.14-slim

WORKDIR /app
RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system && pip uninstall -y pipenv

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
