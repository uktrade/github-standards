"""A module that defines project wide config."""

import os


RELEASE_CHECK_URL = "https://api.github.com/repos/uktrade/github-standards/releases/latest"
PRE_COMMIT_FILE = ".pre-commit-config.yaml"
SIGNED_OFF_BY_TRAILER = "Signed-off-by: DBT pre-commit check"
MANDATORY_HOOK_IDS = ["validate-security-scan", "run-security-scan"]
FORCE_HOOK_CHECKS = os.getenv("FORCE_HOOK_CHECKS", "0")

GITHUB_ACTION_PR = "pr"
GITHUB_ACTION_REPO = "repo"

# Trufflehog
TRUFFLEHOG_ERROR_CODE = 183
TRUFFLEHOG_VERBOSE_LOG_LEVEL = 5
TRUFFLEHOG_INFO_LOG_LEVEL = -1
