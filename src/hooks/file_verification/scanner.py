import asyncio
import re


from anyio import Path, open_file
from io import StringIO
from typing import List

from src.hooks.config import (
    BLOCKED_FILE_EXTENSION_REGEX,
    FILE_VERIFICATION_EXCLUSIONS_FILE_PATH,
    LOGGER,
    MAX_FILE_SIZE_BYTES,
)

logger = LOGGER


class FileVerificationScanResult:
    def __init__(self, forbidden: List[str] | None = None, exceeds_file_size: List[str] | None = None) -> None:
        self.forbidden = forbidden if forbidden else []
        self.exceeds_file_size = exceeds_file_size if exceeds_file_size else []

    def __str__(self) -> str:
        with StringIO() as output_buffer:
            output_buffer.write("--------FILE VERIFICATION SCAN SUMMARY--------")

            if not self.forbidden and not self.exceeds_file_size:
                output_buffer.write("No file verification issues detected")
                return output_buffer.getvalue()

            if self.forbidden:
                output_buffer.write("\n\nFILES WITH A FORBIDDEN FILE EXTENSION\n")
                for forbidden in self.forbidden:
                    output_buffer.write(forbidden)
                    output_buffer.write("\n")

            if self.exceeds_file_size:
                output_buffer.write("\n\nFILES THAT EXCEED THE MAXIMUM FILE SIZE\n")
                for exceeds in self.exceeds_file_size:
                    output_buffer.write(exceeds)
                    output_buffer.write("\n")
            output_buffer.write(
                "\nTO EXCLUDE THESE FILES FROM BEING SCANNED, FOLLOW THE INSTRUCTIONS AT https://github.com/uktrade/github-standards?tab=readme-ov-file#excluding-false-positives-2"
            )
            return output_buffer.getvalue()


class FileVerificationScanner:
    def __init__(
        self,
        verbose: bool = False,
        paths: List[str] | None = None,
    ) -> None:
        self.verbose = verbose
        self.paths = paths if paths else []

    def _is_path_blocked(self, path: str, file_extension_regex: list[str]):
        return any(re.search(regex, path) for regex in file_extension_regex)

    async def _check_file_size_exceeds_maximum(self, path: str, results: list[str]):
        stat_result = await Path(path).stat()
        if stat_result.st_size > MAX_FILE_SIZE_BYTES:
            logger.debug(
                "Path %s has a file size of %s which is above the maximum of %s",
                path,
                stat_result.st_size,
                MAX_FILE_SIZE_BYTES,
            )
            results.append(path)

    async def _get_exclusions(self, exclusions_file: str) -> list[str]:
        exclusions = []

        if not await Path(exclusions_file).exists():
            logger.debug("The file verification exclusions file %s is not present", exclusions_file)
            return exclusions

        async with await open_file(exclusions_file) as f:
            async for exclusion in f:
                exclusions.append(exclusion.rstrip())

        logger.debug("Loaded exclusions from file %s", FILE_VERIFICATION_EXCLUSIONS_FILE_PATH)
        return exclusions

    async def _get_paths_to_scan(self, paths) -> list[str]:
        exclusions = await self._get_exclusions(exclusions_file=FILE_VERIFICATION_EXCLUSIONS_FILE_PATH)

        if not exclusions:
            return paths

        paths_to_scan = []
        for path in paths:
            if path in exclusions:
                logger.debug("Path %s is excluded from file verification scan", path)
                continue
            paths_to_scan.append(path)
        return paths_to_scan

    async def scan(self) -> FileVerificationScanResult:
        blocked_file_extension_paths: list[str] = []
        exceeds_file_size_paths: list[str] = []
        tasks: list[asyncio.Task] = []

        async with asyncio.TaskGroup() as tg:
            for path in await self._get_paths_to_scan(self.paths):
                match = self._is_path_blocked(path, BLOCKED_FILE_EXTENSION_REGEX)
                if match:
                    logger.debug("Path %s has a forbidden file extension", path)
                    blocked_file_extension_paths.append(path)

                tasks.append(tg.create_task(self._check_file_size_exceeds_maximum(path, exceeds_file_size_paths)))

        return FileVerificationScanResult(blocked_file_extension_paths, exceeds_file_size_paths)
