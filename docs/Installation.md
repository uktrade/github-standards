# Installation of this hook

To use these hooks in your own repo:

1. Install the `pre-commit` package using whatever package manager you're using. Alternatively, you can test without a package manager using `pip install pre-commit`
1. Copy the `example.pre-commit-config` file from this repository into the root of your repository, and rename to `.pre-commit-config`. If you already have the `pre-commit` package setup, you can copy the contents of the `example.pre-commit-config` file without the parent `repos` element
1. Run `pre-commit install --install-hooks --overwrite -t commit-msg -t pre-commit` to install both hooks for your repository

# FAQ

## My PR is failing due to a github action checking a Signed-off-by trailer

- Have you run your commit with the `--no-verify` argument? If so this will skip the security scans and the validation hooks needed to pass the github action
- Have you installed the pre-commit commit-msg hook? To check this, open your repository and check the ./hooks folder. There should be a file named `commit-msg` that is ran by the pre-commit framework
