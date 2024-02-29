ifeq ($(shell which python3),)
  PYTHON = python
else
  PYTHON = python3
endif

.DEFAULT_GOAL := help

all: ## run all, yamcs-up (yamcs-down) and yamcs-simulator
	$(MAKE) yamcs-simulator

all-10hz: 
        $(MAKE) yamcs-simulator-10hz

yamcs-up: | yamcs-down ## bring up yamcs system
	docker-compose up -d

yamcs-down: ## bring down yamcs system
	docker-compose down -v --remove-orphans

yamcs-simulator: yamcs-up ## run yamcs simulator
	@echo "connect via http://localhost:8090/ system make take about 50 seconds to startup" && \
        export SIMULATOR_PLAYBACK_RATE="${SIMULATOR_PLAYBACK_RATE}:-1"
	cd .. && $(PYTHON) ./simulator.py

yamcs-simulator-10-hz: yamcs-up ## run yamcs simulator
        @echo "connect via http://localhost:8090/ system make take about 50 seconds to startup" && \
        export SIMULATOR_PLAYBACK_RATE="${SIMULATOR_PLAYBACK_RATE}:-1"
        cd .. && $(PYTHON) ./simulator.py --rate=10


yamcs-shell: ## shell into yamcs container
	docker-compose up -d && docker run -it yamcs "bash"

help:
	@printf "\033[37m%-30s\033[0m %s\n" "#----------------------------------------------------------------------------------"
	@printf "\033[37m%-30s\033[0m %s\n" "# Makefile                                          "
	@printf "\033[37m%-30s\033[0m %s\n" "#----------------------------------------------------------------------------------"
	@printf "\033[37m%-30s\033[0m %s\n" "#-targets----------------------description-----------------------------------------"
	@grep -E '^[a-zA-Z_-].+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

print-%:
	@echo $* = $($*)
