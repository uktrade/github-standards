import sys
import tomllib
import yaml


from logging import StreamHandler, captureWarnings, DEBUG

from src.hooks.config import LOGGER

logger = LOGGER
PROJECT_TOML_FILE = "./pyproject.toml"
PRE_COMMIT_HOOKS_FILE = "./.pre-commit-hooks.yaml"


def main():
    captureWarnings(True)

    logger.setLevel(DEBUG)
    handler = StreamHandler(sys.stderr)
    logger.addHandler(handler)

    with open(PROJECT_TOML_FILE, "rb") as f:
        contents = tomllib.load(f)

        version = contents["project"]["version"]
        logger.debug(
            "Loaded pyproject.toml with version %s",
            version,
        )

    expected_entry = f"ghcr.io/uktrade/github-standards:{version}"
    with open(PRE_COMMIT_HOOKS_FILE, "r", encoding="utf-8") as file:
        hooks = yaml.safe_load(file)
        for hook in hooks:
            if expected_entry not in hook["entry"]:
                logger.debug(
                    "Hook %s contains version %s, but the project.toml file contains %s",
                    hook["id"],
                    hook["entry"],
                    version,
                )
                return 1
            logger.debug(
                "Hook %s contains version %s",
                hook["id"],
                hook["entry"],
            )

    logger.debug("All hooks have the correct versions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
