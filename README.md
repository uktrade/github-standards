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
- [Trufflehog](#trufflehog)
  - [Detectors](#detectors)
  - [Excluding false positives](#excluding-false-positives)
  - [Upgrading trufflehog](#upgrading-trufflehog)
- [Presidio](#presidio)
  - [Excluding false positives](#excluding-false-positives-1)
- [Bandit](#bandit)
  - [Upgrading bandit](#upgrading-bandit)
- [File verification](#file-verification)
  - [Excluding false positives](#excluding-false-positives-2)
- [GitHub actions](#github-actions)
  - [Testing changes](#testing-changes)
- [FAQ](#faq)
  - [My PR is failing due to a github action checking a Signed-off-by trailer](#my-pr-is-failing-due-to-a-github-action-checking-a-signed-off-by-trailer)
  - [I'm receiving errors updating the rev version](#im-receiving-errors-updating-the-rev-version)
  - [I'm seeing pre-commit hooks run multiple times in the logs](#im-seeing-pre-commit-hooks-run-multiple-times-in-the-logs)

# Features

- A set of custom pre-commit hooks, built using python that run security and personal data checks on git commits. Commits containing secrets, tokens or personal data are blocked at a local level.
- Uses the [pre-commit](https://pre-commit.com/index.html) framework to run scans in response to local git hook events
- Distributed as a docker image, hosted in GHCR for ease of installation in a git repository

# Installation

1. Install uv following these instructions https://docs.astral.sh/uv/getting-started/installation/
1. Run `uv sync` to create a local virtual environment and install all dependencies
1. Make sure the venv created by uv is activated in the terminal before running any additional commands
1. Install trufflehog using `brew install trufflehog`

# Testing

## Testing hooks locally

While developing hooks, there are multiple ways of verifying these on your local machine before raising a PR:

### Running the hook command using python

As the hooks are written using python, it is possible to call the python file containing the hook directly, passing the same arguments the pre-commit library would pass. There is a make command `validate-hook-python` that will run this in verbose mode and write debug messages to the terminal.

For the run-security-scan hook, the command would look like this, where `--files` can be one or more filenames to scan: `python3 -m src.hooks.cli run_scan --verbose --files Dockerfile`

### Running the hooks using docker

As the hooks are run using a docker image within other repositories, it is a good idea to test your changes by building and running them using a local docker image.
There is a make command for each of the hooks, that will build and run that hook for you with the correct arguments.
For the run hook it is `make run-hook-docker`.
For the validate hook it is `make validate-hook-docker`.

## Testing hooks from an external repository

Using the pre-commit `try-repo` command, it is possible to test hooks locally in an external repo before releasing a new version.

### Testing pre-commit hooks

The pre-commit hooks receive a list of filenames that have changed in the commit as an argument. To test this hook locally, you need to pass a filename(s) to the hook using this command:
`pre-commit try-repo ../github-standards run-security-scan --hook-stage pre-commit --verbose --files Makefile`

### Testing commit-msg hooks

The commit-msg hook stage is passes a single parameter, which is the name of the file containing the current commit message. To test this locally, you need a file created with the contents being the commit message you want to test. For convenience, a test file has been added to tests/data that can be used with the below command
`pre-commit try-repo ../github-standards validate-security-scan --hook-stage commit-msg --commit-msg-filename tests/test_data/COMMIT_MSG.txt --verbose --all-files -v`

# Releasing

There is a github workflow that will automatically create a new docker tag, and a github release when a change to the `version` tag inside the `pyproject.toml` file is detected. When a new version needs to be released:

1. Open the `pyproject.toml` file, and update the `version` tag to a new value. We use semantic versioning, see [this article](https://www.geeksforgeeks.org/software-engineering/introduction-semantic-versioning/) for help determining what the new version value should be
2. Run `uv sync` to ensure the package is set to the correct version
3. Open a PR into main. Once approved, merging will trigger a new release

You will now have:

- A github release using the new version, set to the be the latest version
- A docker image build and deployed to our [container registry](https://github.com/uktrade/github-standards/pkgs/container/github-standards)

# Usage

To use these hooks inside your project, some initial installation needs to be completed. Once installed, the hooks are self validating and will check for new releases each time they are run, with alerts when you need to upgrade.

If you are already using the pre-commit framework in your project, then follow these instructions. If you are not using the pre-commit framework in your project, then follow these instructions instead

### My project is already using the pre-commit framework

1. Copy the yaml config for the `https://github.com/uktrade/github-standards` repo from the [example.pre-commit-config.yaml](./example.pre-commit-config.yaml) file into to the `.pre-commit-config` file in your repository
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

OR

### My project is not using the pre-commit framework

1. Install the `pre-commit` package using whatever package manager you're using. Alternatively, you can test without a package manager using `pip install pre-commit`. `pre-commit` can be installed as a dev dependency, it is not needed as a build requirement
1. Copy the [example.pre-commit-config.yaml](./example.pre-commit-config.yaml) file from this repository into the root of your repository, and rename to `.pre-commit-config`.
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

## Post installation setup

We use git tags for versioning, once you have copied the yaml to the `.pre-commit-config` file in your repository you need to make sure the `rev` property is set to the latest released version (in the example this is set to `main`). You can check the [releases page](https://github.com/uktrade/github-standards/releases) to get the latest tag to use in place of `main`.

## Optional hooks

There are a large number of pre-commit hooks that can be used to help with code quality and catching linting failures early. This page contains a list of some featured hooks https://pre-commit.com/hooks.html

# Trufflehog

We use a pinned version of trufflehog inside our security scanner.
When building the security scanner docker image locally, the version must be passed as a build arg using `--build-arg TRUFFLEHOG_VERSION=3.90.8` as an example. The Makefile file contains a hardcoded trufflehog version, this is only present for building locally it is not used for any released code

## Detectors

We only use a pre-approved list of trufflehog detectors. Each allowed detector must extend the abstract class `AllowedTrufflehogVendor` and implement 2 methods:

- `code`: This code has to match the value trufflehog has assigned to this vendor, you can find the list at https://github.com/trufflesecurity/trufflehog/blob/main/proto/detectors.proto
- `endpoints`: This is a list of the endpoints this vendor is allowed to call to verify a token is valid. To find a list of endpoints used by this vendor, you need to inspect the trufflehog source code. Starting at https://github.com/trufflesecurity/trufflehog/tree/main/pkg/detectors, find the name of the vendor you are adding. Inside the folder matching that name, you will find a `VENDOR_NAME.go` file that will contain an endpoint url at the top of the file that is used for verification. When adding this to the new vendor class, you need to remove any scheme or port and just paste the domain. E.g For Datadog the `datadogtoken.go` file has the endpoint `https://api.datadoghq.com`, but we add it as `api.datadoghq.com`

## Excluding false positives

If trufflehog has detected a potential secret in your code during a scan that you know is a false positive, you can exclude this from future trufflehog scans. Trufflehog only allows exclusions of an entire file, you cannot exclude individual secrets. To exclude a file from trufflehog:

- If this file doesn't already exist, create a file at the root of the repository called `security-exclusions.txt`
- This file contains list of regexes to exclude from trufflehog, separated by a newline. Add the filename in your repository you want to exclude as a new entry in this file

## Upgrading trufflehog

When an upgrade to trufflehog is required

1. Open the [repository variables](https://github.com/uktrade/github-standards/settings/variables/actions) page in github
1. Edit the TRUFFLEHOG_VERSION variable and set it to the new desired version. This version must have a corresponding image tag on the [trufflehog dockerhub page](https://hub.docker.com/r/trufflesecurity/trufflehog/tags)
1. Create a new github release following the [release instructions](#releasing)

# Presidio

To limit the risk of personal data leaks, we use Microsoft Presidio for scanning files to detect any personal information such as email address and name.

## Excluding false positives

If Presidio has detected potential personal data in your repo during a scan that you know is a false positive, you can exclude this from future Presidio scans. Presidio only allows exclusions of an entire file, you cannot exclude individual lines. To exclude a file from Presidio:

- If this file doesn't already exist, create a file at the root of the repository called `personal-data-exclusions.txt`
- This file contains list of regexes to exclude from Presidio, separated by a newline. Add the filename in your repository you want to exclude as a new entry in this file

# Bandit

Bandit is used for scanning python repositories to find common security issues. Bandit scans are performed using an org level github action, and focused on finding high severity issues that require immediate developer attention when a PR is raised

## Upgrading bandit

Although bandit provides a [github action](https://github.com/PyCQA/bandit-action) that can run scans during a PR being raised, this action always installs the latest version. As part of a cyber condition for using bandit, we are required to use a pinned version so a custom bandit job has been added to the `org.python-ci.yml` file in this repo.

There is a `bandit-version` `env` variable in this job, that is used to install a specific bandit version. This variable must match a github [release version](https://github.com/PyCQA/bandit/releases)

# File verification

Files being committed to GitHub are scanned to ensure they:

1. Do not have a file extension that is forbidden
2. Do not have a filesize above the GitHub recommended limit of 1MB

## Excluding false positives

If the file verification scan has detected a file that you know is a false positive, you can exclude this from future file verification scans. To exclude a file:

- If this file doesn't already exist, create a file at the root of the repository called `file-verifications-exclusions.txt`
- This file contains list of regexes to exclude, separated by a newline. Add the filename in your repository you want to exclude as a new entry in this file

# GitHub actions

This repository contains GitHub actions that are triggered by a set of GitHub Rulesets defined at the organisation level. Any repository in the uktrade organisation can opt in to using these GitHub actions by adding GitHub Custom properties to the repository.

## Testing changes

As this github-standards repository uses the GitHub Custom properties, during a PR for this repository the workflows that are run are the version in the main branch. This makes it difficult to test changes to the workflows, as although the files exist in this repo, any changes to them will not take effect until the PR is merged into main. At that point, any issues with the workflow will be present in all repositories using the GitHub Custom properties.

As these workflow runs aren't visible on the PR screen, you need to use view the GitHub actions filter found [here](https://github.com/uktrade/github-standards/.github/actions?query=event%3Apush)
To solve this, an additional GitHub action on_push trigger has been added to each of the org wide workflows. This trigger will fire on any push event where an org wide workflow yaml file has changed. When raising a PR, the same GitHub workflow will now appear multiple times when a change to a workflow yaml file is made. Once which is the required status enforced by the GitHub Ruleset and is using the workflow version in the main branch, and a second run which is the workflow version in the branch raising the PR.

# FAQ

## My PR is failing due to a github action checking a Signed-off-by trailer

- Have you run your commit with the `--no-verify` argument? If so this will skip the security scans and the validation hooks needed to pass the github action
- Have you installed the pre-commit commit-msg hook? To check this, open your repository and check the ./hooks folder. There should be an executable file named `commit-msg` that is ran by the pre-commit framework

## I'm receiving errors updating the rev version

- Try running `pre-commit gc` and `pre-commit clean` to remove any previous cached versions pre-commit has locally

## I'm seeing pre-commit hooks run multiple times in the logs

The scans run using the https://github.com/uktrade/github-standards repo are scoped to run across defined git hook stages, controlled via a config file inside this repo. However if you are using other pre-commit hooks, for example the ruff formatter, you may see these scans appear multiple times. Adding a `stages` array to your `.pre-commit-config.yaml` file can solve this, where the value is [pre-commit]
