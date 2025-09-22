test-coverage: 
	COVERAGE_FILE=.coverage pytest --cov-report html:htmlcov --cov=./

build-docker:
	docker build . -t dbt-hooks:dev

validate-hook:
	hooks-cli --hook-id=validate-security-scan --verbose

run-hook:
	hooks-cli --hook-id=run-security-scan --verbose