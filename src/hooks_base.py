import logging
import yaml

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


from src.config import PRE_COMMIT_FILE


logger = logging.getLogger()


class Hook(ABC):
    def __init__(self, files: List[str] = []):
        self.files = files

    @abstractmethod
    def validate_args(self) -> bool:
        raise NotImplementedError()

    def _skip_check(self) -> bool:
        """If this check is ran in the dbt-hooks repository, it will always fail as we use a local hook implementation for running the pre-commit hooks. This ensures we are always running the latest local version, and will catch any development errors early before creating a tagged docker image as part of releasing.

        Returns:
            bool: Whether this check should be skipped
        """
        return "site-packages" not in __file__

    def validate_hook_settings(self) -> bool:
        if self._skip_check():
            logger.debug("This hook is being run inside the dbt-hooks repo, the validate hooks settings can be ignored")
            return True

        if not Path(PRE_COMMIT_FILE).exists():
            logger.info("File %s does not exist in this repository. This file must be present", PRE_COMMIT_FILE)
            return False

        with open(PRE_COMMIT_FILE, "r") as file:
            config = yaml.safe_load(file)

            if "repos" not in config:
                logger.info("File %s does not contain a repo tag", PRE_COMMIT_FILE)
                return False

            dbt_hook_repo = list(filter(lambda x: "https://github.com/uktrade/dbt-hooks" in x["repo"], config["repos"]))
            if not dbt_hook_repo:
                logger.info("File %s does not contain the dbt hooks repo", PRE_COMMIT_FILE)
                return False
            if len(dbt_hook_repo) != 1:
                logger.info("File %s can only contain one dbt-hooks repo entry", PRE_COMMIT_FILE)
                return False

            return self._validate_hook_settings(dbt_hook_repo[0])

    @abstractmethod
    def _validate_hook_settings(self, dbt_repo_config) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> bool:
        raise NotImplementedError()
