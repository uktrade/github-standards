# This value is only used in local dev, see README.md for how to upgrade deployed versions of trufflehog
TRUFFLEHOG_VERSION=3.90.12

test: 
	pytest -rP

coverage: 
	COVERAGE_FILE=.coverage pytest --cov-report html:htmlcov --cov=./

build-docker:
	docker build --build-arg TRUFFLEHOG_VERSION=${TRUFFLEHOG_VERSION} . -t github-standards-hooks:dev --target release

build-docker-testing:
	docker build --build-arg TRUFFLEHOG_VERSION=${TRUFFLEHOG_VERSION} . -t github-standards-hooks:testing --target testing

validate-hook-python:
	echo 'Hello world' >> ./tests/EXAMPLE_COMMIT_MSG.txt && hooks-cli validate_scan --verbose ./tests/EXAMPLE_COMMIT_MSG.txt

validate-hook-docker:
	# the EXAMPLE_COMMIT_MSG.txt file is created inside the Dockerfile using the testing target
	make build-docker-testing
	echo 'Hello world commit message' > tests/EXAMPLE_COMMIT_MSG.txt
	docker run --rm -v .:/src:rw,Z -w /src github-standards-hooks:testing validate_scan --verbose tests/EXAMPLE_COMMIT_MSG.txt

run-hook-python:
	hooks-cli run_scan --verbose ./src

run-hook-docker:
	make build-docker-testing
	docker run --rm -v .:/src:rw,Z -w /src github-standards-hooks:testing run_scan --verbose src/hooks/cli.py

run-hook-docker-github-action:
	make build-docker-testing
	docker run --rm -v .:/src:rw,Z -w /src github-standards-hooks:testing run_scan --verbose --github-action /src
