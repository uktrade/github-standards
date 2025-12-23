import asyncio
import aiohttp
import git

from pathlib import Path
from typing import List


from src.hooks.config import (
    LOGGER,
    PERSONAL_DATA_SCAN,
    PRE_COMMIT_FILE,
    RELEASE_CHECK_URL,
    SECURITY_SCAN,
)
from src.hooks.hooks_base import Hook, HookRunResult
from src.hooks.presidio.scanner import PresidioScanResult, PresidioScanner
from src.hooks.trufflehog.scanner import TrufflehogScanResult, TrufflehogScanner
from src.hooks.trufflehog.vendors import AllowedTrufflehogVendor

logger = LOGGER


class RunSecurityScanResult(HookRunResult):
    def __init__(
        self,
        trufflehog_scan_result: TrufflehogScanResult,
        presidio_scan_result: PresidioScanResult,
    ):
        self.trufflehog_scan_result = trufflehog_scan_result
        self.presidio_scan_result = presidio_scan_result

    def run_success(self) -> bool:
        is_success = True
        if self.trufflehog_scan_result:
            if self.trufflehog_scan_result.detected_keys is not None:
                is_success = False
        if self.presidio_scan_result:
            if (
                self.presidio_scan_result.paths_containing_personal_data
                and len(self.presidio_scan_result.paths_containing_personal_data) > 0
            ):
                is_success = False
        return is_success

    def run_summary(self) -> str | None:
        trufflehog_summary = ""
        presidio_summary = ""
        if self.trufflehog_scan_result:
            trufflehog_summary = str(self.trufflehog_scan_result)

        if self.presidio_scan_result:
            presidio_summary = str(self.presidio_scan_result)

        return "".join(["\n", trufflehog_summary, "\n", "\n", presidio_summary])


class RunSecurityScan(Hook):
    def __init__(
        self,
        paths: List[str] = [],
        verbose: bool = False,
        github_action: bool = False,
        excluded_scans: List[str] | None = None,
    ):
        super().__init__(paths, verbose)
        self.github_action = github_action
        self.excluded_scans = excluded_scans if excluded_scans else []

    def validate_args(self) -> bool:
        if self.github_action:
            if self.paths is None:
                logger.debug("No paths passed to hook, this hook needs a directory as the only path")
                return False
            if len(self.paths) != 1:
                logger.debug("This hook needs a directory as the only path, there are %s paths provided", len(self.paths))
                return False
            if not Path(self.paths[0]).is_dir():
                logger.debug(
                    "This hook needs a directory as the only path, the path %s provided is not a directory", self.paths[0]
                )
                return False
            return True

        if self.paths is None or len(self.paths) == 0:
            logger.debug("No paths passed to hook, this hook needs at least 1 paths")
            return False

        return True

    def _get_client_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            base_url="https://api.github.com",
            headers={
                "Accept": "application/vnd.github+json",
            },
        )

    async def _get_version_from_remote(self):
        session = self._get_client_session()
        # This is a low timeout, we don't want to block commits or make devs wait for the github api
        timeout = aiohttp.ClientTimeout(total=1)
        async with session.get(RELEASE_CHECK_URL, raise_for_status=True, timeout=timeout) as response:
            logger.debug("Received %s response from %s", response.status, response.real_url)
            json_content = await response.json()
            await session.close()
            return json_content["tag_name"]

    async def _validate_hook_settings(self, dbt_repo_config):
        if "rev" not in dbt_repo_config:
            logger.debug(
                "File %s contains the github standards hooks repo, but is missing the rev child element", PRE_COMMIT_FILE
            )
            return False

        # If the call to get the remote version fails, return True as we don't want this to block a dev from committing in this scenario.
        try:
            version_in_config = dbt_repo_config["rev"]
            version_in_remote = await self._get_version_from_remote()

            if version_in_config != version_in_remote:
                logger.error(
                    "The version in your local config is %s, but the latest version is %s. Run `pre-commit autoupdate --repo https://github.com/uktrade/github-standards` to update to the latest version",
                    version_in_config,
                    version_in_remote,
                )
        except Exception:
            logger.exception("The remote version check failed", stack_info=True)

        return True

    async def run_security_scan(self) -> TrufflehogScanResult:
        return await TrufflehogScanner(
            self.verbose,
            self.paths,
        ).scan(
            self.github_action,
            AllowedTrufflehogVendor.all_endpoints(),
            AllowedTrufflehogVendor.all_vendor_codes(),
        )

    async def run_personal_scan(self) -> PresidioScanResult:
        paths_to_scan = self.paths
        if self.github_action:
            repo = git.Repo(self.paths[0])
            logger.debug("Scanning files in git repository %s", repo)
            paths_to_scan = [entry.abspath for entry in repo.tree().traverse()]

        return await PresidioScanner(
            self.verbose,
            paths_to_scan,
        ).scan()

    async def run(self) -> RunSecurityScanResult:
        security_scan_task = None
        personal_data_scan_task = None

        async with asyncio.TaskGroup() as tg:
            if SECURITY_SCAN not in self.excluded_scans:
                logger.debug("Running security scan")
                security_scan_task = tg.create_task(self.run_security_scan())
            else:
                logger.debug("Security scan is excluded")

            if PERSONAL_DATA_SCAN not in self.excluded_scans:
                logger.debug("Running personal data scan")
                personal_data_scan_task = tg.create_task(self.run_personal_scan())
            else:
                logger.debug("Personal data scan is excluded")

        security_scan_result = security_scan_task.result() if security_scan_task else None
        personal_data_scan_result = personal_data_scan_task.result() if personal_data_scan_task else None

        return RunSecurityScanResult(
            trufflehog_scan_result=security_scan_result,
            presidio_scan_result=personal_data_scan_result,
        )
