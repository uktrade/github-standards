import os
import subprocess

from typing import List

from src.hooks.config import (
    LOGGER,
    TRUFFLEHOG_ERROR_CODE,
    TRUFFLEHOG_INFO_LOG_LEVEL,
    TRUFFLEHOG_VERBOSE_LOG_LEVEL,
)

logger = LOGGER


class TrufflehogScanner:
    def __init__(
        self,
        verbose: bool = False,
        github_action: bool = False,
        files: List[str] | None = [],
        allowed_vendor_codes: List[str] = [],
    ) -> None:
        self.verbose = verbose
        self.github_action = github_action
        self.files = files
        self.allowed_vendor_codes = allowed_vendor_codes

    def _get_args(self) -> List[str]:
        trufflehog_log_level = TRUFFLEHOG_VERBOSE_LOG_LEVEL if self.verbose else TRUFFLEHOG_INFO_LOG_LEVEL

        if self.github_action:
            # Scan all files in this branch
            files_to_scan = ["file://"]
            scan_mode = "git"
        else:
            # Scan the files passed in
            scan_mode = "filesystem"
            files_to_scan = self.files

        trufflehog_cmd_args = [
            "trufflehog",
            scan_mode,
            "--fail",
            "--no-update",
            "--results=verified,unknown",
            f"--log-level={trufflehog_log_level}",
        ]

        if os.path.exists("trufflehog-excludes.txt"):
            logger.debug("This repo has an exclusions file, adding this file to the trufflehog runner")
            trufflehog_cmd_args.append("--exclude-paths=trufflehog-excludes.txt")

        trufflehog_detectors = ",".join(self.allowed_vendor_codes)
        logger.debug(
            "A subset of detectors have been configured, using these instead of running all detectors: %s",
            trufflehog_detectors,
        )
        trufflehog_cmd_args.append(f"--include-detectors={trufflehog_detectors}")

        trufflehog_cmd_args.extend(files_to_scan)  # type: ignore

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

        if trufflehog_run.returncode == TRUFFLEHOG_ERROR_CODE:
            logger.debug("Trufflehog security scan failed with result: %s", trufflehog_response)
            return trufflehog_response

        logger.debug("Trufflehog security scan successfully completed with result: %s", trufflehog_response)
        return None
