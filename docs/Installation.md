# Installation

## Already using pre-commit?

1. Copy the yaml config for the `https://github.com/uktrade/github-standards` repo from the [example.pre-commit-config.yaml](../example.pre-commit-config.yaml) file into to the `.pre-commit-config` file in your repository
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

## Need to add pre-commit?

1. Install the `pre-commit` package using whatever package manager you're using. Alternatively, you can test without a package manager using `pip install pre-commit`. `pre-commit` can be installed as a dev dependancy, it is not needed as a build requirement
1. Copy the [example.pre-commit-config.yaml](../example.pre-commit-config.yaml) file from this repository into the root of your repository, and rename to `.pre-commit-config`.
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both entry points for your repository

## Using the correct version

We use git tags for versioning, once you have copied the yaml to the `.pre-commit-config` file in your repository you need to make sure the `rev` property is set to the latest released version (in the example this is set to `main`). You can check the [releases page](https://github.com/uktrade/github-standards/releases) to get the latest tag to use in palce of `main`.

## Optional hooks

There are a large number of pre-commit hooks that can be used to help with code quality and catching linting failures early. This page contains a list of some featured hooks https://pre-commit.com/hooks.html
