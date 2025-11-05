# Table of contents

- [Table of contents](#table-of-contents)
- [Features](#features)
- [Installation](#installation)
- [Testing](#testing)
  - [Testing hooks locally](#testing-hooks-locally)
    - [Running the hook command using python](#running-the-hook-command-using-python)
    - [Running the hooks using docker](#running-the-hooks-using-docker)
  - [Testing hooks from an external repository](#testing-hooks-from-an-external-repository)
    - [Testing pre-commit hooks](#testing-pre-commit-hooks)
    - [Testing commit-msg hooks](#testing-commit-msg-hooks)
- [Releasing](#releasing)
- [Usage](#usage)
  - [My project is already using the pre-commit framework](#my-project-is-already-using-the-pre-commit-framework)
  - [My project is not using the pre-commit framework](#my-project-is-not-using-the-pre-commit-framework)
  - [Post installation setup](#post-installation-setup)
  - [Optional hooks](#optional-hooks)
- [FAQ](#faq)
  - [My PR is failing due to a github action checking a Signed-off-by trailer](#my-pr-is-failing-due-to-a-github-action-checking-a-signed-off-by-trailer)
  - [I'm receiving errors updating the rev version](#im-receiving-errors-updating-the-rev-version)

# Features

- A set of custom pre-commit hooks, built using python that run security and personal data checks on git commits. Commits containing secrets, tokens or personal data are blocked at a local level.
- Uses the [pre-commit](https://pre-commit.com/index.html) framework to run scans in response to local git hook events
- Distributed as a docker image, hosted in GHCR for ease of installation in a git repository

# Installation

1. Install uv following these instructions https://docs.astral.sh/uv/getting-started/installation/
1. Run `uv sync` to create a local virtual environment and install all dependencies

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

# Usage

To use these hooks inside your project, some inital installation needs to be completed. Once installed, the hooks are self validating and will check for new releases each time they are run, with alerts when you need to upgrade.

If you are already using the pre-commit framework in your project, then follow these instructions. If you are not using the pre-commit framework in your project, then follow these instructions instead

### My project is already using the pre-commit framework

1. Copy the yaml config for the `https://github.com/uktrade/github-standards` repo from the [example.pre-commit-config.yaml](./example.pre-commit-config.yaml) file into to the `.pre-commit-config` file in your repository
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

OR

### My project is not using the pre-commit framework

1. Install the `pre-commit` package using whatever package manager you're using. Alternatively, you can test without a package manager using `pip install pre-commit`. `pre-commit` can be installed as a dev dependancy, it is not needed as a build requirement
1. Copy the [example.pre-commit-config.yaml](./example.pre-commit-config.yaml) file from this repository into the root of your repository, and rename to `.pre-commit-config`.
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

## Post installation setup

We use git tags for versioning, once you have copied the yaml to the `.pre-commit-config` file in your repository you need to make sure the `rev` property is set to the latest released version (in the example this is set to `main`). You can check the [releases page](https://github.com/uktrade/github-standards/releases) to get the latest tag to use in place of `main`.

## Optional hooks

There are a large number of pre-commit hooks that can be used to help with code quality and catching linting failures early. This page contains a list of some featured hooks https://pre-commit.com/hooks.html

# FAQ

## My PR is failing due to a github action checking a Signed-off-by trailer

- Have you run your commit with the `--no-verify` argument? If so this will skip the security scans and the validation hooks needed to pass the github action
- Have you installed the pre-commit commit-msg hook? To check this, open your repository and check the ./hooks folder. There should be an executable file named `commit-msg` that is ran by the pre-commit framework

## I'm receiving errors updating the rev version

- Try running `pre-commit gc` and `pre-commit clean` to remove any previous cached versions pre-commit has locally
