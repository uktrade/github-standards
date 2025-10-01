import logging
import os
import requests
import subprocess

from configparser import ConfigParser, NoSectionError

from src.hooks.config import (
    GITHUB_ACTION_PR,
    GITHUB_ACTION_REPO,
    PRE_COMMIT_FILE,
    RELEASE_CHECK_URL,
    TRUFFLEHOG_ERROR_CODE,
    TRUFFLEHOG_INFO_LOG_LEVEL,
    TRUFFLEHOG_VERBOSE_LOG_LEVEL,
)
from src.hooks.hooks_base import Hook, HookRunResult
from typing import List

logger = logging.getLogger()


class RunSecurityScan(Hook):
    def __init__(self, files: List[str] | None = None, verbose: bool = False, github_action: str | None = None):
        super().__init__(files, verbose)
        self.github_action = github_action

    def validate_args(self) -> bool:
        if self.github_action:
            logger.debug("The hook is running in github_action mode, all files will be scanned")
            return True

        if self.files is None or len(self.files) == 0:
            logger.debug("No files passed to hook, this hook needs at least 1 file")
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

        # If the call to get the remote version fails, return True as we don't want this to block a dev from commiting in this scenario.
        try:
            version_in_config = dbt_repo_config["rev"]
            version_in_remote = self._get_version_from_remote()

            if version_in_config != version_in_remote:
                logger.info(
                    "The version in your local config is %s, but the latest version is %s. Run `pre-commit autoupdate` to update to the latest version",
                    version_in_config,
                    version_in_remote,
                )
                return False
        except Exception:
            logger.exception("The remote version check failed", stack_info=True)
            return True

        return True

    def _get_trufflehog_detectors(self) -> str | None:
        config = ConfigParser()
        config.read(".config")
        try:
            logger.debug("Config read from %s", ".config")
            return config.get("trufflehog", "DETECTORS")
        except (KeyError, NoSectionError) as exc:
            logger.exception(exc)
            return None

    def run(self) -> HookRunResult:
        trufflehog_log_level = TRUFFLEHOG_VERBOSE_LOG_LEVEL if self.verbose else TRUFFLEHOG_INFO_LOG_LEVEL

        logger.info("Trufflehog excludes file exists: %s", os.path.exists("trufflehog-excludes.txt"))

        if self.github_action == GITHUB_ACTION_PR:
            files_to_scan = ["."]
        elif self.github_action == GITHUB_ACTION_REPO:
            files_to_scan = ["file://./"]
        else:
            files_to_scan = self.files
        scan_mode = "git" if self.github_action == GITHUB_ACTION_REPO else "filesystem"

        trufflehog_cmd_args = [
            "trufflehog",
            scan_mode,
            "--fail",
            "--no-update",
            "--results=verified,unknown",
            f"--log-level={trufflehog_log_level}",
        ]

        trufflehog_detectors = self._get_trufflehog_detectors()
        if trufflehog_detectors:
            logger.debug(
                "A subset of detectors have been configured, using these instead of running all detectors: %s",
                trufflehog_detectors,
            )
            trufflehog_cmd_args.append(f"--include-detectors={trufflehog_detectors}")
        else:
            logger.debug("Running trufflehog with all detectors")

        if os.path.exists("trufflehog-excludes.txt"):
            logger.debug("This repo has an exclusions file, adding this file to the trufflehog runner")
            trufflehog_cmd_args.append("--exclude-paths=trufflehog-excludes.txt")

        trufflehog_cmd_args.extend(files_to_scan)  # type: ignore

        logger.debug("Running trufflehog command '%s'", " ".join(trufflehog_cmd_args))
        trufflehog_run = subprocess.run(
            trufflehog_cmd_args,
            text=True,
            capture_output=True,
            shell=False,
            check=False,  # We are manually checking the response code of the trufflehog scan, setting check=True will raise an exception
        )

        trufflehog_response = trufflehog_run.stdout if trufflehog_run.stdout else trufflehog_run.stderr
        logger.debug("Trufflehog returncode was '%s'", trufflehog_run.returncode)

        if trufflehog_run.returncode == TRUFFLEHOG_ERROR_CODE:
            logger.debug("Trufflehog security scan failed with result: %s", trufflehog_response)
            return HookRunResult(False, trufflehog_response)

        logger.debug("Trufflehog security scan successfully completed with result: %s", trufflehog_response)
        return HookRunResult(True)
