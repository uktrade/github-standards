test-coverage: 
	COVERAGE_FILE=.coverage pytest --cov-report html:htmlcov --cov=./

build-docker:
	docker build . -t dbt-hooks:dev

build-docker-local-testing:
	docker build . -t dbt-hooks:local-testing --target local-testing --file local.Dockerfile

validate-hook-python:
	echo 'Hello world' >> ./tests/EXAMPLE_COMMIT_MSG.txt && hooks-cli --hook-id=validate-security-scan --verbose ./tests/EXAMPLE_COMMIT_MSG.txt

validate-hook-docker:
	# the EXAMPLE_COMMIT_MSG.txt file is created inside the Dockerfile using the local-testing target
	make build-docker-local-testing
	docker run --rm dbt-hooks:local-testing --hook-id validate-security-scan --verbose EXAMPLE_COMMIT_MSG.txt

run-hook-python:
	hooks-cli --hook-id=run-security-scan --verbose

run-hook-docker:
	make build-docker-local-testing
	docker run --rm dbt-hooks:local-testing --hook-id run-security-scan src/hooks/run_security_scan.py