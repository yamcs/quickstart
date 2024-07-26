ifeq ($(shell which python3),)
  PYTHON = python
else
  PYTHON = python3
endif

.DEFAULT_GOAL := help

define print_message
	@printf "\033[32m$1\033[0m\n"
endef

all: clean ## run all, clean, yamcs-up (yamcs-down) and yamcs-simulator
	$(MAKE) yamcs-simulator
  
yamcs-up: | yamcs-down ## bring up yamcs system
	docker compose up -d

yamcs-down: ## bring down yamcs system
	docker compose down -v --remove-orphans

yamcs-simulator: yamcs-up ## run yamcs simulator
	@echo "connect via http://localhost:8090/ system make take about 50 seconds to startup" && \
	cd .. && $(PYTHON) ./simulator.py

yamcs-shell: ## shell into yamcs container
	docker compose up -d && docker compose exec yamcs bash

clean: ## remove yamcs build artifacts and Docker resources created by this Makefile
	$(call print_message, "Stopping any running docker-yamcs containers...")
	docker compose down -v --remove-orphans
	$(call print_message, "Cleaning up docker-yamcs resources (containers, volumes, networks)...")
	docker compose rm -f -s -v
	$(call print_message, "Removing docker-yamcs image...")
	docker image rm -f docker-yamcs || true
	$(call print_message, "Cleaning up yamcs build artifacts...")
	rm -rf ../target
	$(call print_message, "Done!")

help:
	$(call print_message, "#----------------------------------------------------------------------------------")
	$(call print_message, "# Makefile                                          ")
	$(call print_message, "#----------------------------------------------------------------------------------")
	$(call print_message, "#-targets----------------------description-----------------------------------------")
	@grep -E '^[a-zA-Z_-].+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

print-%:
	@echo $* = $($*)
	