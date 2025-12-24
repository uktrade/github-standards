import re

from anyio import open_file, Path
from enum import Enum
from typing import List


from src.hooks.config import (
    DEFAULT_FILE_TYPES,
    LOGGER,
)

logger = LOGGER


class PathScanStatus(Enum):
    SKIPPED = 1
    EXCLUDED = 2
    PASSED = 3
    FAILED = 4


class PathFilter:
    LINE_BY_LINE_FILE_EXTENSIONS = [".csv"]

    def _is_path_excluded(self, path: str, exclusions: List[re.Pattern[str]]):
        for exclusion in exclusions:
            match = exclusion.search(path)
            if match is not None:
                logger.info("Path %s matches regex %s and should be excluded", path, exclusion)
                return True

        logger.debug("The path %s was not found in any exclusion regexes", path)
        return False

    async def _check_is_path_invalid(self, path: str, exclusions: List[re.Pattern[str]]):
        if self._is_path_excluded(path, exclusions):
            return PathScanStatus.EXCLUDED

        if not await Path(path).exists():
            logger.debug("Path %s does not exist", path)
            return PathScanStatus.SKIPPED

        if not await Path(path).is_file():
            logger.debug("Path %s is a directory, presidio can only scan files", path)
            return PathScanStatus.SKIPPED

        file_extension = Path(path).suffix
        if file_extension not in DEFAULT_FILE_TYPES:
            logger.debug(
                "Path %s has an extension that is not accepted for scanning. The allowed paths are %s",
                path,
                DEFAULT_FILE_TYPES,
            )
            return PathScanStatus.SKIPPED

        logger.debug(
            "Path %s is valid and should be scanned",
            path,
        )
        return None

    async def _get_exclusions(self, exclusions_file: str) -> List[re.Pattern[str]]:
        exclusions = []

        if not await Path(exclusions_file).exists():
            logger.debug("The exclusions file %s is not present", exclusions_file)
            return exclusions

        async with await open_file(exclusions_file) as f:
            async for exclusion_regex in f:
                try:
                    regex = re.compile(exclusion_regex.rstrip())
                    exclusions.append(regex)

                except re.error:
                    logger.error(
                        "The regex %s in file %s could not be compiled into a valid regex", exclusion_regex, exclusions_file
                    )
                    raise
        return exclusions
