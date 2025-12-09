from io import StringIO
from anyio import open_file
import json
from pathlib import Path
from typing import List

from presidio_analyzer import AnalyzerEngine, RecognizerResult, AnalyzerEngineProvider
from prettytable import PrettyTable

from src.hooks.config import (
    ENGINE_CONFIG_FILE,
    DEFAULT_LANGUAGE_CODE,
    LOGGER,
    NLP_CONFIG_FILE,
    RECOGNIZER_CONFIG_FILE,
)
from src.hooks.presidio.spacy_post_processing_recognizer import SpacyPostProcessingRecognizer
from src.hooks.presidio.path_filter import PathFilter

logger = LOGGER


class PersonalDataDetection:
    def __init__(self, result: RecognizerResult, text_value: str | None = None) -> None:
        self.result = result
        self.text_value = text_value

    def __repr__(self) -> str:
        return json.dumps({"type": self.result.entity_type, "value": self.text_value})


class PathScanResult:
    def __init__(self, path: str, results: List[PersonalDataDetection]) -> None:
        self.path = path
        self.results = results


class PresidioScanResult:
    def __init__(
        self,
    ) -> None:
        self.valid_path_scans: List[PathScanResult] = []
        self.invalid_path_scans: List[PathScanResult] = []

    def add_scan_result(self, scan_result: PathScanResult):
        if not scan_result.results or len(scan_result.results) == 0:
            self.valid_path_scans.append(scan_result)
        else:
            self.invalid_path_scans.append(scan_result)

    def __str__(self) -> str:
        heading = "--------PERSONAL DATA SCAN SUMMARY--------"
        with StringIO() as output_buffer:
            output_buffer.write(heading)
            if self.valid_path_scans:
                output_buffer.write("\n\nFILES WITHOUT PERSONAL DATA\n")
                paths_without_issues_table = PrettyTable(["Path"])
                for valid_path in self.valid_path_scans:
                    paths_without_issues_table.add_row([valid_path.path])
                output_buffer.write(str(paths_without_issues_table))

            if self.invalid_path_scans:
                output_buffer.write("\n\nFILES CONTAINING PERSONAL DATA\n")

                for invalid_path_scan in self.invalid_path_scans:
                    output_buffer.write(f"\n{invalid_path_scan.path}\n")
                    table = PrettyTable(["Type", "Value", "Score"])
                    for invalid_path in invalid_path_scan.results:
                        table.add_row(
                            [
                                invalid_path.result.entity_type,
                                invalid_path.text_value,
                                invalid_path.result.score,
                            ]
                        )
                    output_buffer.write(str(table))
                    output_buffer.write("\n")
            return output_buffer.getvalue()


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
        base_path = Path(__file__).parent
        provider = AnalyzerEngineProvider(
            analyzer_engine_conf_file=Path.joinpath(base_path, ENGINE_CONFIG_FILE),
            nlp_engine_conf_file=Path.joinpath(base_path, NLP_CONFIG_FILE),
            recognizer_registry_conf_file=Path.joinpath(base_path, RECOGNIZER_CONFIG_FILE),
        )
        analyzer = provider.create_engine()
        analyzer.registry.add_recognizer(SpacyPostProcessingRecognizer())

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

    async def _scan_path(
        self,
        analyzer: AnalyzerEngine,
        entities: List[str],
        file_path: str,
    ) -> PathScanResult:
        file_extension = Path(file_path).suffix.lower()
        async with await open_file(file_path, "r", encoding="utf-8") as fs:
            results: List[PersonalDataDetection] = []
            if file_extension in self.LINE_BY_LINE_FILE_EXTENSIONS:
                logger.debug("Scanning file %s line by line", file_path)
                async for line in fs:
                    results.extend(self._scan_content(analyzer, entities, line.rstrip()))
            else:
                contents = await fs.read()
                logger.debug("Scanning file %s by reading all contents", file_path)
                results.extend(self._scan_content(analyzer, entities, contents))
            return PathScanResult(
                file_path,
                results=results,
            )

    async def scan(
        self,
        github_action: bool = False,
    ) -> PresidioScanResult:
        sources = PathFilter(self.verbose)

        analyzer = self._get_analyzer()
        entities = analyzer.get_supported_entities()

        scan_result = PresidioScanResult()

        async for path in sources.get_paths_to_scan(self.paths, github_action):
            path_scan_result = await self._scan_path(analyzer, entities, path)
            scan_result.add_scan_result(path_scan_result)
        return scan_result
