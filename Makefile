default: help


.PHONY: test
test: .env  ## Run test suite
	docker-compose run --rm httpcheck pytest tests


.PHONY: system-test
system-test: .env  ## Run test suite
	docker-compose run --rm httpcheck python3 ./tests/system.py


.PHONY: build
build: .env  ## Build wheel
	docker-compose run --rm httpcheck python3 ./setup.py bdist_wheel -d build


.PHONY: build-docker
build-docker: .env  ## Build wheel
	docker build --tag httpcheck:latest .


.env:
	touch .env

.PHONY: help
help:  ## Display this help message
	@grep -E '^[a-zA-Z_%.-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36mmake %-16s\033[0m %s\n", $$1, $$2}'
