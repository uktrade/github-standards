import yaml

from anyio import open_file, Path
from abc import ABC, abstractmethod
from typing import List


from src.hooks.config import FORCE_HOOK_CHECKS, LOGGER, PRE_COMMIT_FILE


logger = LOGGER


class HookRunResult(ABC):
    @abstractmethod
    def run_success(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def run_summary(self) -> str | None:
        raise NotImplementedError()


class Hook(ABC):
    def __init__(self, paths: List[str] = [], verbose: bool = False):
        self.paths = paths
        self.verbose = verbose

    @abstractmethod
    def validate_args(self) -> bool:
        raise NotImplementedError()

    def _enforce_settings_checks(self) -> bool:
        """If this check is run in the github-standards repository or in a github action, it will always fail as
        there is no .pre-commit-config.yaml available. For this reason, we skip the checks on that file

        Returns:
            bool: Whether this check should be skipped
        """
        return FORCE_HOOK_CHECKS == "1"

    async def validate_hook_settings(self) -> bool:
        if not self._enforce_settings_checks():
            logger.debug(
                "This hook is running in environment where the validate hooks settings can be ignored. This is either when running as a github action, or when being run inside the github-standards repository as a local pre-commit hook"
            )
            return True

        if not await Path(PRE_COMMIT_FILE).exists():
            logger.debug("File %s does not exist in this repository. This file must be present", PRE_COMMIT_FILE)
            return False

        async with await open_file(PRE_COMMIT_FILE, "r", encoding="utf-8") as file:
            config = yaml.safe_load(await file.read())

            if "repos" not in config:
                logger.debug("File %s does not contain a repo tag", PRE_COMMIT_FILE)
                return False

            dbt_hook_repo = list(
                filter(lambda x: "https://github.com/uktrade/github-standards" in x["repo"], config["repos"])
            )

            if not dbt_hook_repo:
                logger.debug("File %s does not contain the github standards hooks repo", PRE_COMMIT_FILE)
                return False

            if len(dbt_hook_repo) != 1:
                logger.debug("File %s can only contain one github-standards repo entry", PRE_COMMIT_FILE)
                return False
            return await self._validate_hook_settings(dbt_hook_repo[0])

    @abstractmethod
    async def _validate_hook_settings(self, dbt_repo_config) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def run(self) -> HookRunResult:
        raise NotImplementedError()
