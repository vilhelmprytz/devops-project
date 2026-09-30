RUN := pipenv run

.PHONY: install lint test data test-data train compare serve docker-build docker-run pi-setup

install:
	pipenv install --dev --deploy

lint:
	$(RUN) ruff check .
	$(RUN) black --check .

test:
	$(RUN) pytest tests/unit

data:
	$(RUN) python -m dgadetect.data

test-data:
	$(RUN) pytest tests/data

train:
	$(RUN) python -m dgadetect.train

compare:
	$(RUN) python -m dgadetect.compare artifacts/metrics.json $(if $(BASELINE),--baseline $(BASELINE))

serve:
	$(RUN) uvicorn dgadetect.api:app --port 8000

docker-build:
	@test -f artifacts/model.skops || (echo "artifacts/model.skops is missing: run 'make data train' first" && exit 1)
	docker build -t dgadetect:dev .

docker-run:
	docker run --rm -p 8000:8000 dgadetect:dev

pi-setup:
	$(RUN) ansible-playbook -i infra/inventory.ini infra/playbook.yml
