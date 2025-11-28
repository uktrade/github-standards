import git
import io
import re

from pathlib import Path
from typing import Iterator, List


from src.hooks.config import (
    DEFAULT_FILE_TYPES,
    LOGGER,
    PRESIDIO_EXCLUSIONS_FILE_PATH,
)

logger = LOGGER


class PathFilter:
    LINE_BY_LINE_FILE_EXTENSIONS = [".csv"]

    def __init__(
        self,
        verbose: bool = False,
    ) -> None:
        self.verbose = verbose

    def _is_path_excluded(self, path: str, exclusions: List[re.Pattern[str]]):
        for exclusion in exclusions:
            match = exclusion.search(path)
            if match is not None:
                logger.info("Path %s matches regex %s and should be excluded", path, exclusion)
                return True

        logger.debug("The path %s was not found in any exclusion regexes", path)
        return False

    def _should_scan_path(self, path: str, exclusions: List[re.Pattern[str]]):
        if self._is_path_excluded(path, exclusions):
            return False

        if not Path(path).exists():
            logger.debug("Path %s does not exist", path)
            return False

        if not Path(path).is_file():
            logger.debug("Path %s is a directory, presidio can only scan files", path)
            return False

        file_extension = Path(path).suffix
        if file_extension not in DEFAULT_FILE_TYPES:
            logger.debug(
                "Path %s has an extension that is not accepted for scanning. The allowed paths are %s",
                path,
                DEFAULT_FILE_TYPES,
            )
            return False

        logger.debug(
            "Path %s is valid and should be scanned",
            path,
        )
        return True

    def _get_exclusions(self, exclusions_file) -> Iterator[re.Pattern[str]]:
        if not Path(exclusions_file).exists():
            logger.debug("The exclusions file %s is not present", exclusions_file)
            return []

        with io.open(exclusions_file, "r", encoding="utf-8") as file:
            for exclusion_regex in file:
                try:
                    yield re.compile(exclusion_regex.rstrip())

                except re.error:
                    logger.error(
                        "The regex %s in file %s could not be compiled into a valid regex", exclusion_regex, exclusions_file
                    )
                    raise

    def get_paths_to_scan(
        self,
        paths: List[str],
        github_action: bool = False,
    ):
        if github_action:
            repo = git.Repo("./")
            logger.debug("Scanning files in git repository %s", repo)
            paths = [entry.path for entry in repo.tree().traverse()]

        exclusions = list(self._get_exclusions(exclusions_file=PRESIDIO_EXCLUSIONS_FILE_PATH))
        logger.debug("Exclusions file loaded with exclusions %s", exclusions)

        for path in paths:
            if self._should_scan_path(path, exclusions):
                yield path
