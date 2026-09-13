# github-standards

<<<<<<< HEAD
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
- [GitHub actions](#github-actions)
  - [Testing changes](#testing-changes)
  - [Signed-off-by trailer check](#signed-off-by-trailer-check)
- [FAQ](#faq)
  - [My PR is failing due to a github action checking a Signed-off-by trailer](#my-pr-is-failing-due-to-a-github-action-checking-a-signed-off-by-trailer)
  - [I'm receiving errors updating the rev version](#im-receiving-errors-updating-the-rev-version)
  - [I'm seeing pre-commit hooks run multiple times in the logs](#im-seeing-pre-commit-hooks-run-multiple-times-in-the-logs)
=======
Security tooling to support the 
[Code Security Framework](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/).
>>>>>>> eae9329 (Add files via upload)

## Overview
This repository bundles two things:

- **Custom pre-commit hooks** that scan your commits locally, using
  [Trufflehog](https://github.com/trufflesecurity/trufflehog) to detect secrets and tokens
  and [Presidio](https://microsoft.github.io/presidio/) to detect personal data. Findings
  cause the relevant local hook to fail, preventing the commit from completing.
- **Reusable, organisation-level GitHub Actions** that any `uktrade` repository can opt in
  to via GitHub Custom Properties, including a backstop action for the local checks. See
  [GitHub Actions](#github-actions) for detail.

This guide is for those who want to use the hooks and github actions. To develop them,
see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Installing pre-commit hooks
The hooks use the [pre-commit](https://pre-commit.com/index.html) framework to run scans in
response to local git hook events. The commit-msg hook also adds a commit trailer that allows 
CI to verify the security checks were run locally before the commit was created.

The hooks are distributed as a Docker image, hosted in GHCR. Once set up, the hooks are 
self-validating: they check for new releases each time they run and alert you when you need to upgrade.

To use these hooks inside your project, some initial installation needs to be completed.

### Prerequisites
A consuming repository needs the following installed for the hooks to run:

- **Python, with `pre-commit` installed** into a Python environment you control. Use
  whichever tool you prefer — for example `uv`, `pip`, or `pipx`. `pre-commit` can be
  installed as a dev dependency; it is not needed as a build or runtime requirement.
- **Docker**, required because the security-scan hooks run from the GHCR-hosted Docker
  image. Trufflehog and Presidio are bundled inside that image, so you do **not** install
  them separately.

### Pre-commit configuration
- Once you have pre-commit installed, adding pre-commit plugins to your project is done with the 
  `.pre-commit-config.yaml` [configuration file](https://pre-commit.com/#adding-pre-commit-plugins-to-your-project).
- If it already exists in your repository, copy over the repository entry from 
  [`example.pre-commit-config.yaml`](./example.pre-commit-config.yaml)
- Otherwise, copy the [`example.pre-commit-config.yaml`](./example.pre-commit-config.yaml) file from 
  this repository into the root of your repository, and rename it to `.pre-commit-config.yaml`.
- Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` 
  to install both entry points for your repository.

### Post-installation setup
We use git tags for versioning. Once you have copied the yaml into `.pre-commit-config.yaml` in your repository, make sure the `rev` property is set to the latest released version (in the example this is set to `main`). You can check the [releases page](https://github.com/uktrade/github-standards/releases) to get the latest tag to use in place of `main`.

### Optional hooks
There are a large number of pre-commit hooks that can be used to help with code quality and catching linting failures early. This page contains a list of some featured hooks [https://pre-commit.com/hooks.html](https://pre-commit.com/hooks.html)

## Security scans
This section explains what each scanner does and how to exclude a file when it reports a
false positive.

### Trufflehog
We use [Trufflehog](https://github.com/trufflesecurity/trufflehog) to detect secrets and
tokens in your commits.

If Trufflehog has detected a potential secret in your code during a scan that you know is a false positive, you can exclude this from future Trufflehog scans. Trufflehog only allows exclusions of an entire file, you cannot exclude individual secrets. To exclude a file from Trufflehog:
- If this file doesn't already exist, create a file at the root of the repository called `security-exclusions.txt`
- This file contains a list of regexes to exclude from Trufflehog, separated by a newline. Add the filename in your repository you want to exclude as a new entry in this file

### Presidio
To limit the risk of personal data leaks, we use Microsoft Presidio for scanning files to detect any personal information such as email address and name.

If Presidio has detected potential personal data in your repo during a scan that you know is a false positive, you can exclude this from future Presidio scans. Presidio only allows exclusions of an entire file, you cannot exclude individual lines. To exclude a file from Presidio:
- If this file doesn't already exist, create a file at the root of the repository called `personal-data-exclusions.txt`
- This file contains a list of regexes to exclude from Presidio, separated by a newline. Add the filename in your repository you want to exclude as a new entry in this file

## GitHub Actions
This repository contains GitHub Actions that are triggered by a set of GitHub Rulesets
defined at the organisation level. Any repository in the `uktrade` organisation can opt in
to using these GitHub Actions by adding GitHub Custom Properties to the repository. The set
of available actions may change over time.

### Common CI
This GitHub action acts as a backstop for the pre-commit hooks: it re-runs the Trufflehog
and Presidio scans and validates the last commit trailer indicating the pre-commit
hook ran (for example, catching commits made with `--no-verify`). If it finds a secret or
personal data, or the expected attestation is missing, the check fails and a comment is posted.
The ruleset then ensures the PR is blocked.

> **⚠️ TO BE REMOVED — the Bandit scan and Terraform workflow below are optional and interim.
> Remove this section once they are replaced by the Datadog Code Security integration.**

<<<<<<< HEAD
Although bandit provides a [github action](https://github.com/PyCQA/bandit-action) that can run scans during a PR being raised, this action always installs the latest version. As part of a cyber condition for using bandit, we are required to use a pinned version so a custom bandit job has been added to the `org.python-ci.yml` file in this repo.

There is a `bandit-version` `env` variable in this job, that is used to install a specific bandit version. This variable must match a github [release version](https://github.com/PyCQA/bandit/releases)

# GitHub Actions

This repository contains GitHub actions that are triggered by a set of GitHub Rulesets defined at the organisation level. Any repository in the uktrade organisation can opt in to using these GitHub actions by adding GitHub Custom properties to the repository.

## Signed-off-by trailer check

The `pre-commit-check` job in `org.common-ci.yml` verifies that commits were made after installing the pre-commit hooks from this repo, since the hooks are what runs the security and personal data scans locally before a commit is allowed. It does this by checking for the `Signed-off-by: DBT pre-commit check` trailer that the commit-msg hook adds to a commit message once the scans pass - a commit without this trailer means the hooks were either not installed, or were bypassed with `--no-verify`.

Not every commit can realistically carry this trailer though. Commits made directly in the GitHub web UI (for example applying a suggested change, or a merge commit created by clicking "Update branch") never run the local hook, so the job needs to tell those apart from a commit that was made locally and skipped the hooks. It does this by walking the PR's commits (following first-parent only, so merged-in history from `main`/`master`/`dev` is ignored) from newest to oldest, skipping over commits that match a known, safe web UI pattern, until it finds the first commit that must be checked. That commit passes if it either came from a PR that was already merged (so it wouldn't have been run through this check locally), or if it contains the trailer. The table below covers every outcome:

| Scenario | Condition | Outcome | Why |
|---|---|---|---|
| Every commit in the PR is an allowed web UI commit | All commits have committer email `noreply@github.com` **and** a message matching an allowed prefix (`Apply suggestion from`, `Apply suggestions from`, `Merge branch '$BASE_REF' into`) | ✅ Pass | Nothing to check, the job exits early |
| Latest non-web-UI commit came from an already-merged PR | `gh pr list --search "$sha" --state merged` returns a non-empty result | ✅ Pass | The commit predates/bypassed the trailer check via a merge, so it's exempted |
| Latest non-web-UI commit has the trailer | Commit message contains `Signed-off-by: DBT pre-commit check` | ✅ Pass | The pre-commit hook was installed and ran correctly |
| Latest non-web-UI commit is missing the trailer | Pre-commit hook wasn't installed/run, no trailer in message | ❌ Fail | This is the case the FAQ bullets above address |
| Web UI commit from `noreply@github.com` with a message that doesn't match any allowed prefix (e.g. a manual file edit made in the browser) | Email matches, but message text doesn't start with an allowed prefix | ❌ Fail (usually) | Not treated as an allowed web UI commit, so it's the commit that gets checked - browser edits don't carry the trailer |
| Non-web-UI committer email, any message | Committer email isn't `noreply@github.com` | Depends on trailer | This is always the commit that gets checked, since it can never match the allow-list |
| Merge commit pulled in via a non-first-parent branch | Commit reachable only through the second parent of a merge | *(ignored)* | `--first-parent` means these commits are never examined |
| PR opened by `dependabot[bot]` | `github.actor == 'dependabot[bot]'` | Skipped entirely | The job doesn't run at all for dependabot PRs |


## Terraform Workflow
=======
### Bandit (opt-in)
Bandit is used for scanning Python repositories to find common security issues. Bandit scans are performed using an org-level GitHub Action, and focused on finding high severity issues that require immediate developer attention when a PR is raised.
>>>>>>> eae9329 (Add files via upload)

### Terraform workflow (opt-in)
The reusable Terraform workflow defined in this repository checks Terraform code in your repository against a number of standard tools: `terraform fmt`, `terraform validate` and `tflint`. If any of these checks do not exit successfully, the job will fail and you will need to make changes to your code to get it through the CI checks. Because a lot of the Terraform modules we use in our code are hosted in private GitHub repositories, we have had to create a GitHub App to allow them to be pulled into the GitHub Action at runtime. Therefore, there are some pre-requisites you must satisfy before this reusable workflow will work on your repository:
- You must grant your repository access to the organisation-level secrets `TERRAFORM_MODULE_ACCESS_APP_ID` and `TERRAFORM_MODULE_ACCESS_PRIVATE_KEY` [here](https://github.com/organizations/uktrade/settings/secrets/actions) - if you do not have access to do this, SRE can facilitate it for you.
- You must grant the GitHub App `uktrade-terraform-module-access` [here](https://github.com/organizations/uktrade/settings/installations/98143778) repository access to both your repository **and** the repository hosting the module your code is using.
- You must select the Terraform (HCL) option in the language custom property on your repository.

## FAQ

### My PR is failing due to a GitHub Action checking a Signed-off-by trailer
- Have you run your commit with the `--no-verify` argument? If so this will skip the security scans and the validation hooks needed to pass the GitHub Action
- Have you installed the pre-commit commit-msg hook? To check this, open your repository and check the `./hooks` folder. There should be an executable file named `commit-msg` that is run by the pre-commit framework

### I'm receiving errors updating the rev version
- Try running `pre-commit gc` and `pre-commit clean` to remove any previous cached versions pre-commit has locally

### I'm seeing pre-commit hooks run multiple times in the logs
The scans run using the [https://github.com/uktrade/github-standards](https://github.com/uktrade/github-standards) repo are scoped to run across defined git hook stages, controlled via a config file inside this repo. However if you are using other pre-commit hooks, for example the ruff formatter, you may see these scans appear multiple times. Adding a `stages` array to your `.pre-commit-config.yaml` file can solve this, where the value is `[pre-commit]`.

## Contributing
Building, testing, releasing, adding Trufflehog detectors, upgrading the bundled tools and
testing workflow changes are all covered in [CONTRIBUTING.md](./CONTRIBUTING.md).
