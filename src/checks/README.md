# What's easy to measure across organisation repositories

These standalone Bash scripts measure the quick, GitHub API-backed parts of the code security checklist. All API calls are **read-only**. Shared code is in [_common.sh](./_common.sh).

## Artefact to build -> script

| Artefact to build | Script |
| --- | --- |
| Custom GitHub Action – checklist engine | None |
| Reusable workflow wrapping the Action | None |
| code-security-ci ruleset | None |
| code_security_enrolled GitHub custom property | [check-code-security-enrolled.sh](./check-code-security-enrolled.sh) |
| Maintainer attestation register | None |
| Maintainer compliance check | None |
| Security configuration check | [check-security-configuration.sh](./check-security-configuration.sh) |
| Datadog PR gates repository ruleset check | [check-datadog-pr-gates.sh](./check-datadog-pr-gates.sh) |
| scs_portfolio check | [check-scs-portfolio.sh](./check-scs-portfolio.sh) |
| PR template check | [check-pr-template.sh](./check-pr-template.sh) |
| SECURITY.md check | [check-no-security-md.sh](./check-no-security-md.sh) |
| CODEOWNERS check | [check-codeowners.sh](./check-codeowners.sh) |
| Team membership check | [check-team-membership-review.sh](./check-team-membership-review.sh) |
| BIST Code Security Checklist template (`code_security_checklist.md`) | None |

## Usage

Requires Bash 4.4+, `gh`, `jq`, `base64`, `awk`. The date check also uses Python 3.7+. Your access must cover the repos
and teams.

```bash
./check-codeowners.sh uktrade/github-standards
EXPECTED_SECURITY_CONFIGURATION_ID=12345 ./check-security-configuration.sh uktrade/example
./list-repo-properties.sh uktrade
```

Check one repo:

```bash
find -name 'check-*.sh' -exec '{}' uktrade/matchlab ';'
```

See [limitations](#limitations) for notes on those fails/errors.

```
FAIL [uktrade/matchlab] code_security_enrolled must be "true"; observed null. No legacy-property fallback.
PASS [uktrade/matchlab] .github/CODEOWNERS has no GitHub diagnostics and names @uktrade/data-matching-service as its valid primary team.
FAIL [uktrade/data-matching-service] Expected one [MEMBERSHIP_REVIEW=YYYY-MM-DD] marker.
PASS [uktrade/matchlab] No SECURITY.md path exists on main.
PASS [uktrade/matchlab] scs_portfolio is populated: Data and AI Services.
PASS [uktrade/matchlab] Datadog PR Gates is present and active; individual gates and branch coverage are not validated.
PASS [uktrade/matchlab] All repository-local PR templates contain "no secret values are present".
ERROR [uktrade/matchlab] Set EXPECTED_SECURITY_CONFIGURATION_ID to the approved positive numeric configuration ID.
```

Measure a check across all repositories visible to your token:

```bash
set -o pipefail
gh api --paginate 'orgs/uktrade/repos?type=all&per_page=100' --jq '.[].full_name' |
  while IFS= read -r repo; do ./check-scs-portfolio.sh "$repo" || continue; done
```

## Limitations

Security configuration reads require an org administrator/security manager. Note that `check-security-configuration.sh` fails when I run it. I also don't know the approved configuration ID.

`check-code-security-enrolled.sh` checks `code_security_enrolled`, which I don't believe is a custom property we actually use.
