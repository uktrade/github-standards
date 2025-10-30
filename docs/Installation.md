# Installation

## Already using pre-commit?

1. Copy the `https://github.com/uktrade/github-standards` repo yaml config from `example.pre-commit-config` into to the `.pre-commit-config` file in your repository
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

## Need to add pre-commit?

1. Install the `pre-commit` package using whatever package manager you're using. Alternatively, you can test without a package manager using `pip install pre-commit`. `pre-commit` can be installed as a dev dependancy, it is not needed as a build requirement
1. Copy the `example.pre-commit-config` file from this repository into the root of your repository, and rename to `.pre-commit-config`.
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

## Optional hooks

There are a large number of pre-commit hooks that can be used to help with code quality and catching linting failures early. This page contains a list of some featured hooks https://pre-commit.com/hooks.html

# Configuration

## Excluding false positives

If trufflehog has detected a potential secret in your code during a scan that you know is a false positive, you can exclude this from future trufflehog scans. Trufflehog only allows exclusions of an entire file, you cannot exclude individual secrets. To exclude a file from trufflehog:

- If it doesn't exist, create a file at the root of the repository called `trufflehog-excludes.txt`
- This file contains list of regexes to exclude from trufflehog, separated by a newline. Add the filename you want to exclude as a new entry in this file
