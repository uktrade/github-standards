# Code Security Checklist

Last updated: 05/10/26

## 1. Contributor controls

Actions each contributor takes for themselves, so everyone knows what the controls are and why they exist.

- [ ] [All internal contributors have read the Code Repository Hardening guidelines](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/)
- [ ] [All internal contributors have completed code security training in the last year](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#security-training)
- [ ] [All internal contributors have reviewed the GitHub Safety Tips on coding in the open](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#github-safety-tips)

## 2. Repository-level controls

Defences set up within the repository itself.

- [x] [A `.pre-commit-config.yaml` file exists so the organisation-approved hooks run before commits](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#pre-commit-hooks)
- [x] [Repository access has been reviewed](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#repository-access)
- [x] [A `CODEOWNERS` file exists so the right people review changes](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#codeowners)
- [x] [The pull request template reminds reviewers to check for secrets](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#pull-request-template)
- [x] [The repository security policy is inherited from the BIST GitHub Security Policy](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#repository-github-policy)
- [x] [The mandatory custom GitHub properties are set](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#custom-github-properties)
- [x] [Advanced CodeQL is set up if the repository accepts PRs from forks (optional)](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#codeql-for-fork-based-prs-optional)

## 3. Organisation-applied controls

Controls applied by an organisation administrator and verified by a repository administrator.

- [x] [The standard GitHub security configuration is applied to the repository](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#github-security-configuration)
- [x] [The default branch protection ruleset is applied to the default branch](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#branch-protection-rules)
- [x] [GitHub Secret Protection is enabled and blocking secrets](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#github-secret-protection)
- [x] [The relevant vulnerability scans are active](https://platform.readme.trade.gov.uk/managed/features/code-security-framework/#vulnerability-scanning)