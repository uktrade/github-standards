# FAQ

## My PR is failing due to a github action checking a Signed-off-by trailer

- Have you run your commit with the `--no-verify` argument? If so this will skip the security scans and the validation hooks needed to pass the github action
- Have you installed the pre-commit commit-msg hook? To check this, open your repository and check the ./hooks folder. There should be an executable file named `commit-msg` that is ran by the pre-commit framework

## I'm receiving errors updating the rev version

- Try running `pre-commit gc` and `pre-commit clean` to remove any previous cached versions pre-commit has locally
