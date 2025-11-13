import os
import subprocess

from typing import List

from src.hooks.config import (
    LOGGER,
    TRUFFLEHOG_INFO_LOG_LEVEL,
    TRUFFLEHOG_SUCCESS_CODE,
    TRUFFLEHOG_VERBOSE_LOG_LEVEL,
)

logger = LOGGER


class TrufflehogScanner:
    def __init__(
        self,
        verbose: bool = False,
        github_action: bool = False,
        paths: List[str] = [],
        allowed_vendor_codes: List[str] = [],
    ) -> None:
        self.verbose = verbose
        self.github_action = github_action
        self.paths = paths
        self.allowed_vendor_codes = allowed_vendor_codes

    def _get_args(self) -> List[str]:
        trufflehog_log_level = TRUFFLEHOG_VERBOSE_LOG_LEVEL if self.verbose else TRUFFLEHOG_INFO_LOG_LEVEL

        if self.github_action:
            # Scan all files in this branch
            paths_to_scan = [f"file://{self.paths[0]}"]
            scan_mode = "git"
        else:
            # Scan the files passed in
            scan_mode = "filesystem"
            paths_to_scan = self.paths

        trufflehog_cmd_args = [
            "trufflehog",
            scan_mode,
            "--fail",
            "--no-update",
            "--results=verified,unknown",
            f"--log-level={trufflehog_log_level}",
        ]

        if self.github_action:
            trufflehog_cmd_args.append("--since-commit=main")

        if os.path.exists("trufflehog-excludes.txt"):
            logger.debug("This repo has an exclusions file, adding this file to the trufflehog runner")
            trufflehog_cmd_args.append("--exclude-paths=trufflehog-excludes.txt")

        trufflehog_detectors = ",".join(self.allowed_vendor_codes)
        logger.debug(
            "A subset of detectors have been configured, using these instead of running all detectors: %s",
            trufflehog_detectors,
        )
        trufflehog_cmd_args.append(f"--include-detectors={trufflehog_detectors}")

        trufflehog_cmd_args.extend(paths_to_scan)  # type: ignore

        logger.debug("Running trufflehog command '%s'", " ".join(trufflehog_cmd_args))

        return trufflehog_cmd_args

    def scan(self, env: dict[str, str] = {}):
        args = self._get_args()

        trufflehog_run = subprocess.run(
            args,
            text=True,
            capture_output=True,
            shell=False,
            check=False,  # We are manually checking the response code of the trufflehog scan, setting check=True will raise an exception
            env=env,
        )

        trufflehog_response = trufflehog_run.stdout if trufflehog_run.stdout else trufflehog_run.stderr
        logger.debug("Trufflehog returncode was '%s'", trufflehog_run.returncode)

        if trufflehog_run.returncode != TRUFFLEHOG_SUCCESS_CODE:
            logger.debug("Trufflehog security scan failed with result: %s", trufflehog_response)
            return trufflehog_response

        logger.debug("Trufflehog security scan successfully completed with result: %s", trufflehog_response)
        return None
