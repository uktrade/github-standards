import os
import subprocess

from pathlib import Path
from proxy import Proxy
from typing import List


from src.hooks.config import (
    DEFAULT_PROXY_DIRECTORY,
    EXCLUSIONS_FILE_PATH,
    LOGGER,
    TRUFFLEHOG_PROXY,
    TRUFFLEHOG_INFO_LOG_LEVEL,
    TRUFFLEHOG_SUCCESS_CODE,
    TRUFFLEHOG_VERBOSE_LOG_LEVEL,
)
from src.proxy.plugins import OutgoingRequestInterceptorPlugin

logger = LOGGER


class TrufflehogScanner:
    def __init__(
        self,
        verbose: bool = False,
        paths: List[str] = [],
    ) -> None:
        self.verbose = verbose
        self.paths = paths

    def _get_args(
        self,
        paths: List[str],
        github_action: bool = False,
        allowed_vendor_codes: List[str] = [],
    ) -> List[str]:
        trufflehog_log_level = TRUFFLEHOG_VERBOSE_LOG_LEVEL if self.verbose else TRUFFLEHOG_INFO_LOG_LEVEL

        if github_action:
            # Scan all files in this branch
            paths_to_scan = [f"file://{paths[0]}"]
            scan_mode = "git"
        else:
            # Scan the files passed in
            scan_mode = "filesystem"
            paths_to_scan = paths

        trufflehog_cmd_args = [
            "trufflehog",
            scan_mode,
            "--fail",
            "--no-update",
            "--results=verified,unknown",
            f"--log-level={trufflehog_log_level}",
        ]

        if github_action:
            trufflehog_cmd_args.append("--since-commit=main")

        if Path("scan-exclusions.txt").exists():
            logger.debug("This repo has an exclusions file, adding this file to the trufflehog runner")
            trufflehog_cmd_args.append(f"--exclude-paths={EXCLUSIONS_FILE_PATH}")

        trufflehog_detectors = ",".join(allowed_vendor_codes)
        logger.debug(
            "A subset of detectors have been configured, using these instead of running all detectors: %s",
            trufflehog_detectors,
        )
        trufflehog_cmd_args.append(f"--include-detectors={trufflehog_detectors}")

        trufflehog_cmd_args.extend(paths_to_scan)  # type: ignore

        logger.debug("Running trufflehog command '%s'", " ".join(trufflehog_cmd_args))

        return trufflehog_cmd_args

    def _get_trufflehog_env_vars(self):
        env = dict(os.environ)
        env["HTTP_PROXY"] = TRUFFLEHOG_PROXY
        env["HTTPS_PROXY"] = TRUFFLEHOG_PROXY
        return env

    def scan(
        self,
        github_action: bool = False,
        allowed_vendor_endpoints: List[str] = [],
        allowed_vendor_codes: List[str] = [],
    ):
        # A cyber condition has been applied to using trufflehog, where the endpoints called by the trufflehog scanner
        # need to be monitored. We don't have that in place currently, so for now use proxy.py running locally and block
        # any requests made by trufflehog that have not been explicitly allowed

        logger.debug("Using the %s folder for storing proxy.py data", DEFAULT_PROXY_DIRECTORY)
        with Proxy(
            port=8899,
            plugins=[OutgoingRequestInterceptorPlugin],
            log_level="ERROR",
            enable_events=False,
            input_args=[
                "--allowed-trufflehog-vendor-endpoints",
                ",".join(allowed_vendor_endpoints),
                "--cache-dir",
                f"{DEFAULT_PROXY_DIRECTORY}/cache",
            ],
            data_dir=DEFAULT_PROXY_DIRECTORY,
            ca_cert_dir=f"{DEFAULT_PROXY_DIRECTORY}/certs",
        ):
            env = self._get_trufflehog_env_vars()

            args = self._get_args(
                self.paths,
                github_action,
                allowed_vendor_codes,
            )

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
