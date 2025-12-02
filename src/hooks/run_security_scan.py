import requests

from pathlib import Path
from prettytable import PrettyTable
from typing import List

from src.hooks.config import (
    LOGGER,
    PERSONAL_DATA_SCAN,
    PRE_COMMIT_FILE,
    RELEASE_CHECK_URL,
    SECURITY_SCAN,
)
from src.hooks.hooks_base import Hook, HookRunResult
from src.hooks.presidio.scanner import PresidioScanner
from src.hooks.trufflehog.scanner import TrufflehogScanner
from src.hooks.trufflehog.vendors import AllowedTrufflehogVendor

logger = LOGGER


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

    def _get_version_from_remote(self):
        req = requests.get(
            RELEASE_CHECK_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=3,  # This is a low timeout, we don't want to block commits or make devs wait for the github api
        )
        req.raise_for_status()
        content = req.json()
        return content["tag_name"]

    def _validate_hook_settings(self, dbt_repo_config):
        if "rev" not in dbt_repo_config:
            logger.debug(
                "File %s contains the github standards hooks repo, but is missing the rev child element", PRE_COMMIT_FILE
            )
            return False

        # If the call to get the remote version fails, return True as we don't want this to block a dev from committing in this scenario.
        try:
            version_in_config = dbt_repo_config["rev"]
            version_in_remote = self._get_version_from_remote()

            if version_in_config != version_in_remote:
                logger.info(
                    "The version in your local config is %s, but the latest version is %s. Run `pre-commit autoupdate --repo https://github.com/uktrade/github-standards` to update to the latest version",
                    version_in_config,
                    version_in_remote,
                )
                return False
        except Exception:
            logger.exception("The remote version check failed", stack_info=True)
            return True

        return True

    def run_security_scan(self):
        scanner = TrufflehogScanner(
            self.verbose,
            self.paths,
        )
        error_response = scanner.scan(
            self.github_action,
            AllowedTrufflehogVendor.all_endpoints(),
            AllowedTrufflehogVendor.all_vendor_codes(),
        )
        if error_response:
            return HookRunResult(False, error_response)
        return HookRunResult(True)

    def run_personal_scan(self):
        scanner = PresidioScanner(
            self.verbose,
            self.paths,
        )

        # TODO
        # File skipped due to file extension
        # File excluded from scan

        scan_results = scanner.scan(
            self.github_action,
        )

        paths_without_issues_table = PrettyTable(["Path"])
        paths_with_issues_count = 0
        for scan_result in scan_results:
            if not scan_result.results or len(scan_result.results) == 0:
                paths_without_issues_table.add_row([scan_result.path])
            else:
                paths_with_issues_count = paths_with_issues_count + 1
                table = PrettyTable(["Type", "Value", "Score"])
                for result in scan_result.results:
                    table.add_row(
                        [
                            result.result.entity_type,
                            result.text_value,
                            result.result.score,
                        ]
                    )
                logger.info("Detections in file %s", scan_result.path)
                logger.info(table)

        logger.info("Scanned paths with no data detected")
        logger.info(paths_without_issues_table)

        if paths_with_issues_count > 0:
            return HookRunResult(False, f"{paths_with_issues_count} files had personal data detected")

        return HookRunResult(True)

    def run(self) -> HookRunResult:
        # A cyber condition has been applied to using trufflehog, where the endpoints called by the trufflehog scanner
        # need to be monitored. We don't have that in place currently, so for now use proxy.py running locally and block
        # any requests made by trufflehog that have not been explicitly allowed
        if SECURITY_SCAN not in self.excluded_scans:
            security_scan_result = self.run_security_scan()
            if security_scan_result.success is False:
                return security_scan_result
        else:
            logger.debug("Security scan is excluded")

        if PERSONAL_DATA_SCAN not in self.excluded_scans:
            personal_data_scan_result = self.run_personal_scan()
            if personal_data_scan_result.success is False:
                return personal_data_scan_result
        else:
            logger.debug("Personal data scan is excluded")

        return HookRunResult(True)
