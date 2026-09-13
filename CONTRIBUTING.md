# Contributing to github-standards

This guide is for developers and maintainers of the hooks and workflows themselves. If you
only want to adopt the hooks in your own repository, see the [README](./README.md) instead.

The repository contains two things that are developed, tested and released in different
ways, so this guide is organised around them:

- **[Part A: the pre-commit hooks](#part-a-the-pre-commit-hooks)** — Python hooks
  distributed as a Docker image and consumed through the pre-commit framework.
- **[Part B: the organisation workflows](#part-b-the-organisation-workflows)** — 
  reusable, organisation-level GitHub Actions triggered by GitHub Rulesets and Custom
  Properties.
- **[Part C: troubleshooting](#part-c-troubleshooting)** — common problems when developing
  or releasing either of the above.

## Table of contents

- [Part A: the pre-commit hooks](#part-a-the-pre-commit-hooks)
  - [Local development setup](#local-development-setup)
  - [Testing hooks locally](#testing-hooks-locally)
    - [Running the hook command using Python](#running-the-hook-command-using-python)
    - [Running the hooks using Docker](#running-the-hooks-using-docker)
  - [Testing hooks from an external repository](#testing-hooks-from-an-external-repository)
    - [Testing pre-commit hooks](#testing-pre-commit-hooks)
    - [Testing commit-msg hooks](#testing-commit-msg-hooks)
  - [Maintaining the bundled scanners](#maintaining-the-bundled-scanners)
    - [Trufflehog](#trufflehog)
    - [Detectors](#detectors)
    - [Upgrading Trufflehog](#upgrading-trufflehog)
  - [Releasing](#releasing)
- [Part B: the organisation workflows](#part-b-the-organisation-workflows)
  - [How the workflows are triggered](#how-the-workflows-are-triggered)
  - [Testing workflow changes](#testing-workflow-changes)
  - [Bandit (optional)](#bandit-optional)
- [Part C: troubleshooting](#part-c-troubleshooting)

## Part A: the pre-commit hooks

### Local development setup

This sets up a local environment to develop the pre-commit hooks. Consumers of the hooks do
not need any of this — the hooks run from the GHCR Docker image (see the
[README](./README.md)).

- Install uv following these instructions
  [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv sync` to create a local virtual environment and install all dependencies
- Make sure the venv created by uv is activated in the terminal before running any
  additional commands
- Install Trufflehog by following the
  [official Trufflehog installation instructions](https://github.com/trufflesecurity/trufflehog#floppy_disk-installation)

### Testing hooks locally

While developing hooks, there are multiple ways of verifying these on your local machine
before raising a PR.

#### Running the hook command using Python

As the hooks are written using Python, it is possible to call the Python file containing the
hook directly, passing the same arguments the pre-commit library would pass. There is a make
command `validate-hook-python` that will run this in verbose mode and write debug messages
to the terminal.

For the `run-security-scan` hook, the command would look like this, where `--files` can be
one or more filenames to scan:

```bash
python3 -m src.hooks.cli run_scan --verbose --files Dockerfile
```

#### Running the hooks using Docker

As the hooks are run using a Docker image within other repositories, it is a good idea to
test your changes by building and running them using a local Docker image. There is a make
command for each of the hooks, that will build and run that hook for you with the correct
arguments:

- For the run hook it is `make run-hook-docker`.
- For the validate hook it is `make validate-hook-docker`.

### Testing hooks from an external repository

Using the `pre-commit try-repo` command, it is possible to test hooks locally in an external
repo before releasing a new version.

#### Testing pre-commit hooks

The pre-commit hooks receive a list of filenames that have changed in the commit as an
argument. To test this hook locally, you need to pass a filename(s) to the hook:

```bash
pre-commit try-repo ../github-standards run-security-scan --hook-stage pre-commit --verbose --files Makefile
```

#### Testing commit-msg hooks

The commit-msg hook stage receives a single argument, which is the name of the file
containing the current commit message. To test this locally, you need a file created with
the contents being the commit message you want to test. For convenience, a test file has
been added to `tests/test_data/` that can be used with the below command:

```bash
pre-commit try-repo ../github-standards validate-security-scan --hook-stage commit-msg --commit-msg-filename tests/test_data/COMMIT_MSG.txt --verbose --all-files -v
```

### Maintaining the bundled scanners

#### Trufflehog

We use a pinned version of Trufflehog inside our security scanner. When building the
security scanner Docker image locally, the version must be passed as a build arg using
`--build-arg TRUFFLEHOG_VERSION=3.90.8` as an example. The Makefile contains a hardcoded
Trufflehog version; this is only present for building locally, it is not used for any
released code.

#### Detectors

We only use a pre-approved list of Trufflehog detectors. Each allowed detector must extend
the abstract class `AllowedTrufflehogVendor` and implement 2 methods:

- **code**: this code has to match the value Trufflehog has assigned to this vendor, you can
  find the list at
  [https://github.com/trufflesecurity/trufflehog/blob/main/proto/detectors.proto](https://github.com/trufflesecurity/trufflehog/blob/main/proto/detectors.proto)
- **endpoints**: this is a list of the endpoints this vendor is allowed to call to verify a
  token is valid. To find a list of endpoints used by this vendor, you need to inspect the
  Trufflehog source code. Starting at
  [https://github.com/trufflesecurity/trufflehog/tree/main/pkg/detectors](https://github.com/trufflesecurity/trufflehog/tree/main/pkg/detectors),
  find the name of the vendor you are adding. Inside the folder matching that name, you will
  find a `VENDOR_NAME.go` file that will contain an endpoint url at the top of the file that
  is used for verification. When adding this to the new vendor class, you need to remove any
  scheme or port and just paste the domain. For example, for Datadog the `datadogtoken.go`
  file has the endpoint `https://api.datadoghq.com`, but we add it as `api.datadoghq.com`

#### Upgrading Trufflehog

When an upgrade to Trufflehog is required:

- Open the [repository variables](https://github.com/uktrade/github-standards/settings/variables/actions)
  page in GitHub
- Edit the `TRUFFLEHOG_VERSION` variable and set it to the new desired version. This version
  must have a corresponding image tag on the
  [Trufflehog dockerhub page](https://hub.docker.com/r/trufflesecurity/trufflehog/tags)
- Create a new GitHub release following the [release instructions](#releasing)

### Releasing

There is a GitHub workflow that will automatically create a new Docker tag, and a GitHub
release, when a change to the version tag inside the `pyproject.toml` file is detected. When
a new version needs to be released:

- Open the `pyproject.toml` file, and update the version tag to a new value. We use semantic
  versioning, see [this article](https://www.geeksforgeeks.org/software-engineering/introduction-semantic-versioning/)
  for help determining what the new version value should be
- Run `uv sync` to ensure the package is set to the correct version
- Open a PR into main. Once approved, merging will trigger a new release

You will now have:

- A GitHub release using the new version, set to be the latest version
- A Docker image built and deployed to our
  [container registry](https://github.com/uktrade/github-standards/pkgs/container/github-standards)

## Part B: the organisation workflows

### How the workflows are triggered

The organisation-level GitHub Actions in this repository are triggered by GitHub Rulesets
defined at the organisation level, and repositories opt in through GitHub Custom Properties.
This means workflow changes take effect organisation-wide as soon as they are merged into
main, so they must be tested on the branch before merge.

There is no local development setup for the workflows: they can only be exercised by pushing
to a branch and inspecting the resulting runs, as described below.

### Testing workflow changes

Because this github-standards repository uses GitHub Custom Properties, the workflows that
run during a PR for this repository are the versions on the main branch. This makes it
difficult to test changes to the workflows: although the files exist in this repo, any
changes to them do not take effect until the PR is merged into main. At that point, any
issues with the workflow would already be present in all repositories using the GitHub
Custom Properties.

To make changes testable before merge, an additional `on_push` trigger has been added to
each of the organisation-wide workflows. This trigger fires on any push event where an
organisation-wide workflow yaml file has changed. As a result, when you raise a PR that
changes a workflow yaml file, the same GitHub workflow appears twice:

- the **ruleset-required run**, which is the status enforced by the GitHub Ruleset and uses
  the workflow version on the main branch; and
- the **branch-triggered test run**, which uses the workflow version on the branch raising
  the PR.

Always check the branch-triggered run when reviewing workflow changes.

### Bandit (optional)

**⚠️ TO BE REMOVED — the Bandit scan is optional and interim. Remove this section once it is
replaced by the Datadog Code Security integration.**

Although Bandit provides a [GitHub Action](https://github.com/PyCQA/bandit-action) that can
run scans during a PR being raised, this action always installs the latest version. As part
of a cyber condition for using Bandit, we are required to use a pinned version, so a custom
Bandit job has been added to the `org.python-ci.yml` file in this repo. There is a
`bandit-version` env variable in this job, that is used to install a specific Bandit
version. This variable must match a Bandit
[release version](https://github.com/PyCQA/bandit/releases).

## Part C: troubleshooting

### I can't see the ruleset-triggered workflow runs on the PR screen

Ruleset-triggered runs are not shown on the PR screen. View them through the GitHub Actions
filter found [here](https://github.com/uktrade/github-standards/.github/actions?query=event%3Apush).

### My workflow change doesn't seem to have taken effect

You are almost certainly looking at the ruleset-required run, which uses the workflow version
on main. Check the branch-triggered test run instead — see
[Testing workflow changes](#testing-workflow-changes).
