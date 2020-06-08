default: help


.PHONY: test
test:   ## Run test suite
	docker-compose run app pytest tests


.PHONY: build
build:  ## Build wheel
	docker-compose run app python ./setup.py bdist_wheel -d build


.PHONY: help
help:  ## Display this help message
	@grep -E '^[a-zA-Z_%.-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36mmake %-16s\033[0m %s\n", $$1, $$2}'
