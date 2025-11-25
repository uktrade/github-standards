"""A module that defines project wide config."""

import os
import logging

RELEASE_CHECK_URL = "https://api.github.com/repos/uktrade/github-standards/releases/latest"
PRE_COMMIT_FILE = ".pre-commit-config.yaml"
SIGNED_OFF_BY_TRAILER = "Signed-off-by: DBT pre-commit check"
MANDATORY_HOOK_IDS = ["validate-security-scan", "run-security-scan"]
FORCE_HOOK_CHECKS = os.getenv("FORCE_HOOK_CHECKS", "0")

LOGGER = logging.getLogger("app")


# Trufflehog
TRUFFLEHOG_EXCLUSIONS_FILE_PATH = "security-exclusions.txt"
TRUFFLEHOG_ERROR_CODE = 183
TRUFFLEHOG_SUCCESS_CODE = 0
TRUFFLEHOG_VERBOSE_LOG_LEVEL = 5
TRUFFLEHOG_INFO_LOG_LEVEL = -1
TRUFFLEHOG_PROXY = "http://localhost:8899"

# Proxy.py
DEFAULT_PROXY_DIRECTORY = os.getenv("DEFAULT_PROXY_DIRECTORY", "./.proxy_py")

# Presidio
DEFAULT_LANGUAGE_CODE = "en"
DEFAULT_FILE_TYPES = [".txt", ".yml", ".yaml", ".csv"]
SPACY_MODEL_NAME = "en_core_web_sm"
SPACY_ENTITIES = ["PERSON"]
PRESIDIO_EXCLUSIONS_FILE_PATH = "personal-data-exclusions.txt"
