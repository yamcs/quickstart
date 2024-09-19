SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTHON := $(shell command -v python3 2>/dev/null || echo python)

.DEFAULT_GOAL := help

# Define function to print messages in different colors
# Usage: $(call print_message,ANSI_COLOR_CODE,Your message here)
define print_message
	@printf "\033[$(1)m$(2)\033[0m\n"
endef

.PHONY: all all-10hz clean yamcs-up yamcs-down yamcs-simulator yamcs-simulator-10hz yamcs-shell help

all: clean yamcs-up yamcs-simulator ## run all: clean, yamcs-up (yamcs-down) and yamcs-simulator

all-10hz: clean yamcs-up yamcs-simulator-10hz ## run all: clean, yamcs-up (yamcs-down) and yamcs-simulator

yamcs-up: | yamcs-down ## bring up yamcs system
	docker compose up -d

yamcs-down: ## bring down yamcs system
	$(call print_message,33,Stopping any running docker-yamcs containers...)
	docker compose down -v --remove-orphans

yamcs-simulator: ## run yamcs simulator
	$(call print_message,36,Connect via http://localhost:8090/ system may take about 50 seconds to startup)
	cd .. && $(PYTHON) ./simulator.py

yamcs-simulator-10hz: ## run yamcs simulator at 10hz
	$(call print_message,36,Connect via http://localhost:8090/ system may take about 50 seconds to startup)
	cd .. && $(PYTHON) ./simulator.py --rate=10

yamcs-simulator-down: ## stop the yamcs simulator
	$(call print_message,33,Stopping the yamcs simulator...)
	pkill -f simulator.py
	$(call print_message,32,Simulator stopped successfully)

yamcs-simulator-restart: yamcs-simulator-down yamcs-simulator ## stop the yamcs simulator and start it again

yamcs-shell: ## shell into yamcs container
	docker compose up -d && docker compose exec yamcs bash

clean: | yamcs-down ## remove yamcs build artifacts and docker resources created by this Makefile
	$(call print_message,33,Cleaning up docker-yamcs resources (containers, volumes, networks)...)
	docker compose rm -f -s -v
	$(call print_message,33,Removing docker-yamcs image...)
	docker image rm -f docker-yamcs 2>/dev/null || true
	$(call print_message,33,Cleaning up yamcs build artifacts...)
	rm -rf ../target
	$(call print_message,32,Done!)

wait-for-sent: | yamcs-up ## run make all and wait up to 10 minutes for "Sent:" in the output
	@echo "Running make all and waiting for 'Sent:' in the output..." && \
	nohup $(MAKE) all > all.log 2>&1 & \
	pid=$$!; \
	timeout=600; \
	while ! grep -q "Sent:" all.log; do \
		sleep 1; \
		timeout=$$((timeout - 1)); \
		if [ $$timeout -le 0 ]; then \
			echo "Timeout waiting for 'Sent:' in the output"; \
			kill $$pid; \
			exit 1; \
		fi; \
	done; \
	echo "Found 'Sent:' in the output"; \
	kill $$pid

TERM_WIDTH := $(shell tput cols 2>/dev/null || echo 80)

define print_header
	@printf '%*s\n' "$(TERM_WIDTH)" '' | tr ' ' '-'
	@printf '%-*s\n' "$(TERM_WIDTH)" "$(1)"
	@printf '%*s\n' "$(TERM_WIDTH)" '' | tr ' ' '-'
endef


help: ## display this help message
	$(call print_header,"Makefile")
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m%-30s\033[0m %s\n", "Target", "Description"} /^[a-zA-Z_-]+:.*?##/ {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

print-%: ## Print any variable (e.g., make print-PYTHON)
	@echo $* = $($*)
