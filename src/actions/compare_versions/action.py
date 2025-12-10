import sys
import tomllib
import yaml


from anyio import run, open_file
from logging import StreamHandler, captureWarnings, DEBUG

from src.hooks.config import LOGGER

logger = LOGGER
PROJECT_TOML_FILE = "./pyproject.toml"
PRE_COMMIT_HOOKS_FILE = "./.pre-commit-hooks.yaml"


async def main_async():
    captureWarnings(True)

    logger.setLevel(DEBUG)
    handler = StreamHandler(sys.stderr)
    logger.addHandler(handler)

    async with await open_file(PROJECT_TOML_FILE, "r") as f:
        contents = tomllib.loads(await f.read())

        version = contents["project"]["version"]
        logger.debug(
            "Loaded pyproject.toml with version %s",
            version,
        )

    expected_entry = f"ghcr.io/uktrade/github-standards:{version}"
    async with await open_file(PRE_COMMIT_HOOKS_FILE, "rb") as file:
        hooks = yaml.safe_load(await file.read())
        for hook in filter(lambda hook: "-development" not in hook["id"], hooks):
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


def main():
    return run(main_async)


if __name__ == "__main__":
    sys.exit(main())
