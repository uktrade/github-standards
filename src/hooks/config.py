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
DEFAULT_FILE_TYPES = [".txt", ".yml", ".yaml", ".csv"]
PRESIDIO_EXCLUSIONS_FILE_PATH = "personal-data-exclusions.txt"

# File verification
FILE_VERIFICATION_EXCLUSIONS_FILE_PATH = "file-verifications-exclusions.txt"
MAX_FILE_SIZE_BYTES = 1024 * 1000
BLOCKED_FILE_EXTENSION_REGEX = [
    # Databases
    r"\.backup$",
    r"\.bak$",
    # Worksheets
    r"\.xlsx$",
    r"\.xls$",
    # Word Legacy
    r"\.doc$",
    r"\.dot$",
    r"\.wbk$",
    #  Word Office Open XML (OOXML) format
    r"\.docx$",
    r"\.docm$",
    r"\.dotx$",
    r"\.dotm$",
    r"\.docb$",
    # Excel
    r"\.xls$",
    r"\.xlt$",
    r"\.xlm$",
    #  Excel OOXML
    r"\.xlsx$",
    r"\.xlsm$",
    r"\.xltx$",
    r"\.xltm$",
    # Other formats
    r"\.xlsb$",
    r"\.xla$",
    r"\.xlam$",
    r"\.xll$",
    r"\.xlw$",
    # PowerPoint legacy
    r"\.ppt$",
    r"\.pot$",
    r"\.pps$",
    # OOXML
    r"\.pptx$",
    r"\.pptm$",
    r"\.potx$",
    r"\.potm$",
    r"\.ppam$",
    r"\.ppsx$",
    r"\.ppsm$",
    r"\.sldx$",
    r"\.sldm$",
    # Access
    r"\.accdb$",
    r"\.accde$",
    r"\.accdt$",
    r"\.accdr$",
    # OneNote
    r"\.one$",
    # Publisher
    r"\.pub$",
    # XPS Document
    r"\.xps$",
    # Adobe
    r"\.pdf$",
    r"\.ps$",
    r"\.eps$"
    r"\.prn$",
    # Secret files
    r"\.p12$",
    r"\.pfx$",
    r"\.pkcs12$",
    r"\.pem$",
    r"_rsa$",
    r"_dsa$",
    r"]_ed25519$",
    r"_ecdsa$",
    r"\.jks$",
    # bash/zsh rc file:
    r"^\.?(bash|zsh)?rc$",
    # bash/zsh profile:
    r"^\.?(bash|zsh)_profile$",
    # bash/zsh aliases file:
    r"^\.?(bash|zsh)_aliases$",
    # credential(s) file:
    r"^\.credential(s)?$",
    # Github Enterprise file:
    r"^\.githubenterprise$",
    # Apple Keychain file:
    r"^\.*keychain$",
    # Keystore/Keyring file:
    r"^key(store|ring)$",
    # Keepass secret file
    r"^\.*kdb",
    # Archive files:
    r"\.zip$",
    r"\.rar$",
    r"\.7z$",
    r"\.tar$",
    r"\.gz$",
    r"\.bz2$",
]
