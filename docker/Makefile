ifeq ($(shell which python3),)
  PYTHON = python
else
  PYTHON = python3
endif

.DEFAULT_GOAL := help

all: ## run all, yamcs-up (yamcs-down) and yamcs-simulator
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

wait-for-sent: yamcs-up ## run make all and wait up to 10 minutes for "Sent:" in the output
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

help:
	@printf "\033[37m%-30s\033[0m %s\n" "#----------------------------------------------------------------------------------"
	@printf "\033[37m%-30s\033[0m %s\n" "# Makefile                                          "
	@printf "\033[37m%-30s\033[0m %s\n" "#----------------------------------------------------------------------------------"
	@printf "\033[37m%-30s\033[0m %s\n" "#-targets----------------------description-----------------------------------------"
	@grep -E '^[a-zA-Z_-].+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

print-%:
	@echo $* = $($*)
