# Setting up this project

Create a new virtual environment using `python -m venv .venv`
Activate it using `source .venv/bin/activate`
Run `pip install -e .`
Run `pip install -r requirements-dev.txt`

## Testing hooks

Using the pre-commit `try-repo` command, it is possible to test hooks locally before release a new version.

### Testing pre-commit hooks

The pre-commit hooks receive a list of filenames that have changed in the commit as an argument. To test this hook locally, you need to pass a filename(s) to the hook using this command:
`pre-commit try-repo ./ run-security-scan --hook-stage pre-commit --verbose --files Makefile`

### Testing commit-msg hooks

The commit-msg hook stage is passes a single parameter, which is the name of the file containing the current commit message. To test this locally, you need a file created with the contents being the commit message you want to test. For convenience, a test file has been added to tests/data that can be used with the below command
`pre-commit try-repo ./ validate-security-scan --hook-stage commit-msg --commit-msg-filename tests/test_data/COMMIT_MSG.txt --verbose --all-files -v`

# Usage in your project

[See installation instructions](docs/Installation.md)
