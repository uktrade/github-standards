# github-standards

Organisation-wide security tooling to support the 
[Code Security Framework](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/).

## Table of contents
- [Installing in your repository](#installing-in-your-repository)
  - [Prerequisites](#prerequisites)
  - [My project is already using the pre-commit framework](#my-project-is-already-using-the-pre-commit-framework)
  - [My project is not using the pre-commit framework](#my-project-is-not-using-the-pre-commit-framework)
  - [Post-installation setup](#post-installation-setup)
  - [Optional hooks](#optional-hooks)
- [Security scans and excluding false positives](#security-scans-and-excluding-false-positives)
  - [Trufflehog](#trufflehog)
  - [Presidio](#presidio)
- [GitHub Actions](#github-actions)
  - [Bandit (optional)](#bandit-optional)
  - [Terraform workflow (optional)](#terraform-workflow-optional)
- [FAQ](#faq)
- [Contributing / developing these hooks](#contributing--developing-these-hooks)

## Overview
This repository bundles two things:

- **Custom pre-commit hooks** that scan your commits locally, using
  [Trufflehog](https://github.com/trufflesecurity/trufflehog) to detect secrets and tokens
  and [Presidio](https://microsoft.github.io/presidio/) to detect personal data. Findings
  cause the relevant local hook to fail, preventing the commit from completing.
- **Reusable, organisation-level GitHub Actions** that any `uktrade` repository can opt in
  to via GitHub Custom Properties, including a backstop action for the local checks. See
  [GitHub Actions](#github-actions) for detail.

## Installing pre-commit hooks
This section covers **adopting the hooks in your own repository**. If instead you want to
set up a local environment to develop the hooks themselves, see
[CONTRIBUTING.md](./CONTRIBUTING.md).

The hooks use the [pre-commit](https://pre-commit.com/index.html) framework to run scans in
response to local git hook events. The hooks are distributed as a Docker image, hosted in GHCR. 
Once set up, the hooks are self-validating: they check for new
releases each time they run and alert you when you need to upgrade.

To use these hooks inside your project, some initial installation needs to be completed.

### Prerequisites
A consuming repository needs the following installed for the hooks to run:

- **Python, with `pre-commit` installed** into a Python environment you control. Use
  whichever tool you prefer — for example `uv`, `pip`, or `pipx`. `pre-commit` can be
  installed as a dev dependency; it is not needed as a build or runtime requirement.
- **Docker**, required because the security-scan hooks run from the GHCR-hosted Docker
  image. Trufflehog and Presidio are bundled inside that image, so you do **not** install
  them separately.

### My project is already using the pre-commit framework
- Copy the repository entry from [`example.pre-commit-config.yaml`](./example.pre-commit-config.yaml) into `.pre-commit-config.yaml` in your repository
- Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

OR

### My project is not using the pre-commit framework
- Make sure `pre-commit` is installed (see [Prerequisites](#prerequisites)).
- Copy the [`example.pre-commit-config.yaml`](./example.pre-commit-config.yaml) file from this repository into the root of your repository, and rename it to `.pre-commit-config.yaml`.
- Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

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

One of these actions acts as a backstop for the pre-commit hooks: it re-runs the Trufflehog
and Presidio scans and validates a commit trailer or attestation indicating the pre-commit
hook ran (for example, catching commits made with `--no-verify`). If it finds a secret or
personal data, or the expected attestation is missing, the check fails and the PR is blocked.

> **⚠️ TO BE REMOVED — the Bandit scan and Terraform workflow below are optional and interim.
> Remove this section once they are replaced by the Datadog Code Security integration.**

### Bandit (optional)
Bandit is used for scanning Python repositories to find common security issues. Bandit scans are performed using an org-level GitHub Action, and focused on finding high severity issues that require immediate developer attention when a PR is raised.

### Terraform workflow (optional)
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

## Contributing / developing these hooks
Building, testing, releasing, adding Trufflehog detectors, upgrading the bundled tools and
testing workflow changes are all covered in [CONTRIBUTING.md](./CONTRIBUTING.md).
