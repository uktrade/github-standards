import asyncio
import json
import re

from io import StringIO
from anyio import open_file
from pathlib import Path
from typing import List

from presidio_analyzer import AnalyzerEngine, RecognizerResult, AnalyzerEngineProvider
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
        self, analyzer: AnalyzerEngine, entities: List[str], file_path: str, exclusions: List[re.Pattern[str]]
    ) -> PathScanResult:
        try:
            sources = PathFilter()

            invalid_check_result = await sources._check_is_path_invalid(file_path, exclusions)
            if invalid_check_result is not None:
                return PathScanResult(file_path, invalid_check_result)

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
                    status=PathScanStatus.PASSED if len(results) == 0 else PathScanStatus.FAILED,
                    results=results,
                )
        except Exception as exc:
            logger.exception("The file scanner failed to read file %s", file_path, stack_info=True)
            return PathScanResult(file_path, status=PathScanStatus.ERRORED, additional_detail=str(exc))

    async def scan(
        self,
    ) -> PresidioScanResult:
        sources = PathFilter()

        analyzer = self._get_analyzer()
        entities = analyzer.get_supported_entities()

        exclusions = await sources._get_exclusions(exclusions_file=PRESIDIO_EXCLUSIONS_FILE_PATH)
        logger.debug("Personal data exclusions file loaded with exclusions %s", exclusions)

        tasks: list[asyncio.Task] = []
        async with asyncio.TaskGroup() as tg:
            for path in self.paths:
                tasks.append(
                    tg.create_task(self._scan_path(analyzer, entities, path, exclusions)),
                )
        scan_result = PresidioScanResult(results=[task.result() for task in tasks])

        return scan_result
