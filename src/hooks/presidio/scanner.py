import io

import json
from pathlib import Path
from typing import Iterator, List

from presidio_analyzer import AnalyzerEngine, RecognizerResult, AnalyzerEngineProvider

from src.hooks.config import (
    CONFIG_FILE,
    DEFAULT_LANGUAGE_CODE,
    LOGGER,
)
from src.hooks.presidio.path_filter import PathFilter

logger = LOGGER


class PersonalDataDetection:
    def __init__(self, result: RecognizerResult, text_value: str | None = None) -> None:
        self.result = result
        self.text_value = text_value

    def __repr__(self) -> str:
        return json.dumps({"type": self.result.entity_type, "value": self.text_value})


class ScanResult:
    def __init__(self, path: str, results: List[PersonalDataDetection]) -> None:
        self.path = path
        self.results = results


class PresidioScanner:
    LINE_BY_LINE_FILE_EXTENSIONS = [".csv"]

    def __init__(
        self,
        verbose: bool = False,
        paths: List[str] = [],
    ) -> None:
        self.verbose = verbose
        self.paths = paths

    def _get_analyzer(self) -> AnalyzerEngine:
        # Set up the engine, loads the NLP module (spaCy model by default)
        # and other PII recognizers
        # Create configuration containing engine name and models

        provider = AnalyzerEngineProvider(analyzer_engine_conf_file=CONFIG_FILE)
        analyzer = provider.create_engine()

        return analyzer

    def _scan_content(self, analyzer: AnalyzerEngine, entities: List[str], content: str):
        results = analyzer.analyze(
            text=content,
            language=DEFAULT_LANGUAGE_CODE,
            entities=entities,
        )
        if results:
            logger.debug("Found presidio results %s", results)
        return [PersonalDataDetection(result, content[result.start : result.end]) for result in results]

    def _scan_path(
        self,
        analyzer: AnalyzerEngine,
        entities: List[str],
        file_path: str,
    ) -> Iterator[ScanResult]:
        file_extension = Path(file_path).suffix.lower()
        with io.open(file_path, "r", encoding="utf-8") as fs:
            results: List[PersonalDataDetection] = []
            if file_extension in self.LINE_BY_LINE_FILE_EXTENSIONS:
                logger.debug("Scanning file %s line by line", file_path)
                for line in fs:
                    results.extend(self._scan_content(analyzer, entities, line.rstrip()))
            else:
                logger.debug("Scanning file %s by reading all contents", file_path)
                results.extend(self._scan_content(analyzer, entities, fs.read()))
            yield ScanResult(
                file_path,
                results=results,
            )

    def scan(
        self,
        github_action: bool = False,
    ) -> Iterator[ScanResult]:
        sources = PathFilter(self.verbose)

        analyzer = self._get_analyzer()
        entities = analyzer.get_supported_entities()

        for path in sources.get_paths_to_scan(self.paths, github_action):
            yield from self._scan_path(analyzer, entities, path)
