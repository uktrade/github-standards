"""A module that defines project wide config."""

import os
import logging

RELEASE_CHECK_URL = "/repos/uktrade/github-standards/releases/latest"
PRE_COMMIT_FILE = ".pre-commit-config.yaml"
SIGNED_OFF_BY_TRAILER = "Signed-off-by: DBT pre-commit check"
MANDATORY_HOOK_IDS = ["validate-security-scan", "run-security-scan"]
FORCE_HOOK_CHECKS = os.getenv("FORCE_HOOK_CHECKS", "0")
SECURITY_SCAN = "security"
PERSONAL_DATA_SCAN = "data"

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

ENGINE_CONFIG_FILE = "engine_config.yaml"
NLP_CONFIG_FILE = "nlp_config.yaml"
RECOGNIZER_CONFIG_FILE = "recognizer_config.yaml"
EXCLUDED_PERSONAL_DATA_FILE_TYPES = [
    # images
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".svg",
]
PRESIDIO_EXCLUSIONS_FILE_PATH = "personal-data-exclusions.txt"
