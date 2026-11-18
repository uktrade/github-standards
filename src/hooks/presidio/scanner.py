from __future__ import annotations

import json
import re

from io import StringIO
from anyio import open_file, to_thread
from pathlib import Path
from typing import TYPE_CHECKING, List

from prettytable import PrettyTable

from src.hooks.config import (
    ENGINE_CONFIG_FILE,
    DEFAULT_LANGUAGE_CODE,
    LOGGER,
    NLP_CONFIG_FILE,
    PRESIDIO_EXCLUSIONS_FILE_PATH,
    RECOGNIZER_CONFIG_FILE,
)
from src.hooks.presidio.path_filter import PathFilter, PathScanStatus

if TYPE_CHECKING:
    # Importing presidio loads spaCy so at runtime it is only imported once a path needs scanning
    from presidio_analyzer import AnalyzerEngine, RecognizerResult

logger = LOGGER


class PersonalDataDetection:
    def __init__(self, result: RecognizerResult, text_value: str | None = None) -> None:
        self.result = result
        self.text_value = text_value

    def __repr__(self) -> str:
        return json.dumps({"type": self.result.entity_type, "value": self.text_value})


class PathScanResult:
    def __init__(
        self,
        path: str,
        status: PathScanStatus,
        results: List[PersonalDataDetection] | None = None,
        additional_detail: str | None = None,
    ) -> None:
        self.path = path
        self.status = status
        self.results = results if results else []
        self.additional_detail = additional_detail


class PresidioScanResult:
    def __init__(self, results: List[PathScanResult] = []) -> None:
        self.paths_without_personal_data: List[PathScanResult] = []
        self.paths_containing_personal_data: List[PathScanResult] = []
        self.paths_skipped: List[PathScanResult] = []
        self.paths_excluded: List[PathScanResult] = []
        self.paths_errored: List[PathScanResult] = []
        self.add_path_scan_results(results)

    def add_path_scan_results(self, scan_results: List[PathScanResult]):
        for scan_result in scan_results:
            self.add_path_scan_result(scan_result)

    def add_path_scan_result(self, scan_result: PathScanResult):
        if scan_result.status == PathScanStatus.EXCLUDED:
            self.paths_excluded.append(scan_result)

        if scan_result.status == PathScanStatus.FAILED:
            self.paths_containing_personal_data.append(scan_result)

        if scan_result.status == PathScanStatus.PASSED:
            self.paths_without_personal_data.append(scan_result)

        if scan_result.status == PathScanStatus.SKIPPED:
            self.paths_skipped.append(scan_result)

        if scan_result.status == PathScanStatus.ERRORED:
            self.paths_errored.append(scan_result)

    def __str__(self) -> str:
        with StringIO() as output_buffer:
            output_buffer.write("--------PERSONAL DATA SCAN SUMMARY--------")
            if self.paths_excluded:
                output_buffer.write("\n\nFILES EXCLUDED\n")
                excluded_paths_table = PrettyTable(["Path"])
                for excluded_path in self.paths_excluded:
                    excluded_paths_table.add_row([excluded_path.path])
                output_buffer.write(str(excluded_paths_table))

            if self.paths_skipped:
                output_buffer.write("\n\nFILES SKIPPED\n")
                skipped_paths_table = PrettyTable(["Path"])
                for skipped_path in self.paths_skipped:
                    skipped_paths_table.add_row([skipped_path.path])
                output_buffer.write(str(skipped_paths_table))

            if self.paths_without_personal_data:
                output_buffer.write("\n\nFILES WITHOUT PERSONAL DATA\n")
                paths_without_issues_table = PrettyTable(["Path"])
                for valid_path in self.paths_without_personal_data:
                    paths_without_issues_table.add_row([valid_path.path])
                output_buffer.write(str(paths_without_issues_table))

            if self.paths_errored:
                output_buffer.write("\n\nFILES ERRORED\n")
                errored_paths_table = PrettyTable(["Path", "Reason"])
                for errored_path in self.paths_errored:
                    errored_paths_table.add_row([errored_path.path, errored_path.additional_detail])
                output_buffer.write(str(errored_paths_table))

            if self.paths_containing_personal_data:
                output_buffer.write("\n\nFILES CONTAINING PERSONAL DATA\n")

                for invalid_path_scan in self.paths_containing_personal_data:
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
                output_buffer.write(
                    "\nTO EXCLUDE THESE FILES FROM BEING SCANNED FOR PERSONAL DATA, FOLLOW THE INSTRUCTIONS AT https://github.com/uktrade/github-standards?tab=readme-ov-file#excluding-false-positives-1"
                )
            return output_buffer.getvalue()


class PresidioScanner:
    LINE_BY_LINE_FILE_EXTENSIONS = [".csv"]

    def __init__(
        self,
        verbose: bool = False,
        paths: List[str] | None = None,
    ) -> None:
        self.verbose = verbose
        self.paths = paths if paths else []

    def _get_analyzer(self) -> AnalyzerEngine:
        from presidio_analyzer import AnalyzerEngineProvider

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
        self._disable_unused_spacy_components(analyzer)

        return analyzer

    def _disable_unused_spacy_components(self, analyzer: AnalyzerEngine):
        from presidio_analyzer.predefined_recognizers import SpacyRecognizer

        # Presidio only reads lemmas (for context words) and named entities from spaCy so the dependency parser is
        # never used. Named entities are only used by NLP-based recognizers (SpacyRecognizer and its subclasses) which
        # are disabled in recognizer_config.yaml. Disabling both roughly halves file scan time
        unused_components = ["parser"]
        if not any(isinstance(recognizer, SpacyRecognizer) for recognizer in analyzer.registry.recognizers):
            unused_components.append("ner")

        nlp = analyzer.nlp_engine.nlp[DEFAULT_LANGUAGE_CODE]
        for component in unused_components:
            if component in nlp.pipe_names:
                logger.debug("Disabling unused spaCy component %s", component)
                nlp.disable_pipe(component)

    def _scan_content(self, analyzer: AnalyzerEngine, entities: List[str], content: str):
        results = analyzer.analyze(
            text=content,
            language=DEFAULT_LANGUAGE_CODE,
            entities=entities,
        )
        if results:
            logger.debug("Found presidio results %s", results)
        return [PersonalDataDetection(result, content[result.start : result.end]) for result in results]

    def _scan_lines(self, analyzer: AnalyzerEngine, entities: List[str], contents: str) -> List[PersonalDataDetection]:
        # Scan all lines in one worker-thread call to avoid a thread hop per line on large files. StringIO splits only
        # on newlines, whereas str.splitlines() would also split on characters such as \f inside a value
        detections: List[PersonalDataDetection] = []
        for line in StringIO(contents):
            detections.extend(self._scan_content(analyzer, entities, line.rstrip()))
        return detections

    async def _scan_path(self, analyzer: AnalyzerEngine, entities: List[str], file_path: str) -> PathScanResult:
        try:
            async with await open_file(file_path, "r", encoding="utf-8") as fs:
                contents = await fs.read()

            file_extension = Path(file_path).suffix.lower()
            if file_extension in self.LINE_BY_LINE_FILE_EXTENSIONS:
                logger.debug("Scanning file %s line by line", file_path)
                results = await to_thread.run_sync(self._scan_lines, analyzer, entities, contents)
            else:
                logger.debug("Scanning file %s by reading all contents", file_path)
                results = await to_thread.run_sync(self._scan_content, analyzer, entities, contents)

            return PathScanResult(
                file_path,
                status=PathScanStatus.PASSED if len(results) == 0 else PathScanStatus.FAILED,
                results=results,
            )
        except Exception as exc:
            logger.exception("The file scanner failed to read file %s", file_path, stack_info=True)
            return PathScanResult(file_path, status=PathScanStatus.ERRORED, additional_detail=str(exc))

    async def _get_unscanned_result(self, path: str, exclusions: List[re.Pattern[str]]) -> PathScanResult | None:
        # Returns the result for a path that won't be scanned or None if the path needs scanning
        try:
            invalid_check_result = await PathFilter()._check_is_path_invalid(path, exclusions)
        except Exception as exc:
            logger.exception("The file scanner failed to read file %s", path, stack_info=True)
            return PathScanResult(path, status=PathScanStatus.ERRORED, additional_detail=str(exc))

        if invalid_check_result is None:
            return None
        return PathScanResult(path, invalid_check_result)

    async def scan(
        self,
    ) -> PresidioScanResult:
        sources = PathFilter()

        exclusions = await sources._get_exclusions(exclusions_file=PRESIDIO_EXCLUSIONS_FILE_PATH)
        logger.debug("Personal data exclusions file loaded with exclusions %s", exclusions)

        # Results stay in path order with None for each path that still needs scanning
        results = [await self._get_unscanned_result(path, exclusions) for path in self.paths]
        if all(result is not None for result in results):
            logger.debug("No paths need a personal data scan, skipping loading the presidio analyzer")
            return PresidioScanResult(results=results)

        # Loading spaCy is CPU-bound so run it in a thread to avoid delaying the trufflehog scan
        analyzer = await to_thread.run_sync(self._get_analyzer)
        entities = analyzer.get_supported_entities()

        for index, path in enumerate(self.paths):
            if results[index] is None:
                results[index] = await self._scan_path(analyzer, entities, path)

        return PresidioScanResult(results=results)
