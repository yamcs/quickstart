

all:
	$(MAKE) yamcs-simulator
	
yamcs-build: ## build yamcs system
	docker build . -t yamcs

yamcs-up: | yamcs-build yamcs-down ## bring up yamcs system
	docker-compose up -d

yamcs-down: ## bring down yamcs system
	docker-compose down -v --remove-orphans

yamcs-simulator: yamcs-up ## run yamcs simulator
	cd .. && python ./simulator.py

yamcs-shell: ## shell into yamcs container
	docker run -it yamcs "bash"