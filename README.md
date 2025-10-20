# Setting up this project

Install uv following these instructions https://docs.astral.sh/uv/getting-started/installation/
Run `uv sync` to create a local virtual environment and install all dependencies

# Testing

## Testing hooks locally

While developing hooks, there are multiple ways of verifying these on your local machine before raising a PR:

### Running the hook command using python

As the hooks are written using python, it is possible to call the python file contain the hook directly passing the same arguments the pre-commit library would pass. There is a make command `validate-hook-python` that will run this in verbose mode and write debug messages to the terminal.

For the run-security-scan hook, the command would look like this, where `--files` can be one or more filenames to scan: `python3 -m src.hooks.cli run_scan --verbose --files Dockerfile`

### Running the hooks using docker

As the hooks are run using a docker image within other repositories, it is a good idea to test your changes by building and running them using a local docker image.
There is a make command for each of the hooks, that will build and run that hook for you with the correct arguments.
For the run hook it is `run-hook-docker`.
For the validate hook it is `validate-hook-docker`.

## Testing hooks from an external repository

Using the pre-commit `try-repo` command, it is possible to test hooks locally in an external repo before releasing a new version.

### Testing pre-commit hooks

The pre-commit hooks receive a list of filenames that have changed in the commit as an argument. To test this hook locally, you need to pass a filename(s) to the hook using this command:
`pre-commit try-repo ../github-standards run-security-scan --hook-stage pre-commit --verbose --files Makefile`

### Testing commit-msg hooks

The commit-msg hook stage is passes a single parameter, which is the name of the file containing the current commit message. To test this locally, you need a file created with the contents being the commit message you want to test. For convenience, a test file has been added to tests/data that can be used with the below command
`pre-commit try-repo ../github-standards validate-security-scan --hook-stage commit-msg --commit-msg-filename tests/test_data/COMMIT_MSG.txt --verbose --all-files -v`

# Releasing

There is a github action that can be run to release a new version of the hooks. To create a new release:

1. Go to https://github.com/uktrade/github-standards/tags and find the latest tag
1. Go to https://github.com/uktrade/github-standards/actions/workflows/release.yml and click the `Run workflow` button. This repository uses semantic versioning, so in the `Version to release` input add the new version
1. Press the `Run workflow` button, wait for the action to finish

You will now have:

- A github release using the new version, set to the be the latest version
- A docker image build and deployed to TBC

# Usage in your project

[See installation instructions](docs/Installation.md)
