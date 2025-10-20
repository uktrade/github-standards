include .local_env

test: 
	pytest -rP

test-coverage: 
	COVERAGE_FILE=.coverage pytest --cov-report html:htmlcov --cov=./

build-docker:
	docker build . -t github-standards-hooks:dev --target release

build-docker-local-testing:
	docker build . -t github-standards-hooks:testing --target testing

validate-hook-python:
	echo 'Hello world' >> ./tests/EXAMPLE_COMMIT_MSG.txt && hooks-cli validate_scan --verbose ./tests/EXAMPLE_COMMIT_MSG.txt

validate-hook-docker:
	# the EXAMPLE_COMMIT_MSG.txt file is created inside the Dockerfile using the local-testing target
	make build-docker-local-testing
	docker run --rm github-standards-hooks:testing validate_scan --verbose EXAMPLE_COMMIT_MSG.txt

run-hook-python:
	hooks-cli run_scan --verbose

run-hook-docker:
	make build-docker-local-testing
	docker run --rm github-standards-hooks:testing run_scan --verbose src/hooks_base.py
