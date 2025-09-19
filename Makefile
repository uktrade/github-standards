test-coverage: 
	COVERAGE_FILE=.coverage pytest --cov-report html:htmlcov --cov=./

build-docker:
	docker build . -t dbt-hooks:dev