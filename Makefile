
PACKAGE=pkm_trade_spoofer

.PHONY: install
install:
	poetry install

.PHONY: install-dev
install-dev:
	poetry install --with dev

.PHONY: gen-req
gen-req:
	@ poetry export -f requirements.txt --output requirements.txt --without-hashes
	@ poetry export --with dev -f requirements.txt --output requirements-dev.txt --without-hashes

.PHONY: run
run:
	python -m pkm_trade_spoofer

.PHONY: format
format:
	poetry run black $(PACKAGE)
	poetry run isort $(PACKAGE)

.PHONY: check
check:
	poetry run mypy --install-types --non-interactive $(PACKAGE)
	poetry run flake8 $(PACKAGE)
