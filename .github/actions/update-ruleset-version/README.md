# Usage

<!-- start usage -->

```yaml
- uses: ./.github/actions/update-ruleset-version
  with:
    # The new tag to use for the rulesets. This tag must exist on the uktrade/github-standards repo
    tag: ""

    # The repository id of the repository containing the workflow yml files used by the rulesets. A ruleset can have multiple rules, only the rules that use the repository id will be updated
    org-repository-id: ""

    # A GitHub token with at least the Administration organization permission. This can be either a PAT or a token from a GitHub app
    token: ""

    # Can be either a single ruleset id, or a comma separated list of ruleset ids. Every id provided will be updated to the new tag
    ruleset-ids: ""
```

<!-- end usage -->
