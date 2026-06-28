.DEFAULT_GOAL := help
PY := .venv/bin/python
PIP := .venv/bin/pip
SERVICE := telegram-summarizer.service
UNIT_DST := $(HOME)/.config/systemd/user

.PHONY: help setup run run-once dry-run discover-chat test lint \
	service-install service-restart service-status logs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Create venv and install runtime + dev dependencies
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

run: ## Run the service in the foreground (Ctrl-C to stop)
	$(PY) -m app.main

run-once: ## Run a single poll cycle and exit (sends replies)
	$(PY) -m app.main --once

dry-run: ## Run a single cycle, printing summaries instead of sending
	$(PY) -m app.main --once --dry-run

discover-chat: ## Print chat ids seen (post in the channel first), nothing is sent
	$(PY) -m app.main --once --dry-run

test: ## Run the pytest suite
	$(PY) -m pytest -q

lint: ## Lint with ruff
	.venv/bin/ruff check app tests

service-install: ## Install + enable + start the systemd user service
	mkdir -p $(UNIT_DST)
	cp systemd/$(SERVICE) $(UNIT_DST)/
	systemctl --user daemon-reload
	systemctl --user enable --now $(SERVICE)
	@echo "Tip: run 'loginctl enable-linger $(USER)' so it runs without an active login."

service-restart: ## Restart the service (after editing .env or code)
	systemctl --user restart $(SERVICE)

service-status: ## Show service status
	systemctl --user --no-pager status $(SERVICE)

logs: ## Tail the application log
	tail -f telegram-summarizer.log
