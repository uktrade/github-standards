import git
import io
import re

from pathlib import Path
from typing import Iterator, List

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from src.hooks.config import (
    DEFAULT_FILE_TYPES,
    DEFAULT_LANGUAGE_CODE,
    PRESIDIO_EXCLUSIONS_FILE_PATH,
    LOGGER,
    SPACY_ENTITIES,
    SPACY_MODEL_NAME,
)

logger = LOGGER


class PersonalDataDetection:
    def __init__(self, filename: str, result: RecognizerResult, text_value: str | None = None) -> None:
        self.filename = filename
        self.result = result
        self.text_value = text_value

    def __repr__(self) -> str:
        return f"Found possible personal data.\nFilename: {self.filename}\nDetected entity: {self.result}\nText value: {self.text_value}"


class PresidioScanner:
    # TODO sort this class out, duplicated _scan_file_contents to quickly get this live but needs redesigning
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
        engine_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": DEFAULT_LANGUAGE_CODE, "model_name": SPACY_MODEL_NAME},
            ],
            "ner_model_configuration": {"labels_to_ignore": ["CARDINAL", "MONEY", "WORK_OF_ART", "FAC"]},
        }

        # Create NLP engine based on configuration
        provider = NlpEngineProvider(nlp_configuration=engine_configuration)
        nlp_engine = provider.create_engine()

        provider = RecognizerRegistryProvider(
            registry_configuration={
                "supported_languages": [DEFAULT_LANGUAGE_CODE],
                "recognizers": [
                    {"name": "EmailRecognizer", "type": "predefined"},
                    # Remove spacy for now, as it false positives comments as person objects
                    {"name": "SpacyRecognizer", "type": "predefined", "supported_entities": SPACY_ENTITIES},
                ],
            },
        )

        analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=[DEFAULT_LANGUAGE_CODE],
            registry=provider.create_recognizer_registry(),
        )

        return analyzer

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

    def _scan_file_contents(
        self,
        analyzer: AnalyzerEngine,
        entities: List[str],
        file_path: str,
    ):
        with io.open(file_path, "r", encoding="utf-8") as fs:
            contents = fs.read()

            results = analyzer.analyze(
                text=contents,
                language=DEFAULT_LANGUAGE_CODE,
                entities=entities,
            )
            for result in results:
                logger.debug(
                    "Result [%s] found",
                    result,
                )
                yield PersonalDataDetection(file_path, result, text_value=contents[result.start : result.end])

    def _scan_line_by_line(
        self,
        analyzer: AnalyzerEngine,
        entities: List[str],
        file_path: str,
    ):
        with io.open(file_path, "r", encoding="utf-8") as fs:
            for line in fs:
                results = analyzer.analyze(
                    text=line,
                    language=DEFAULT_LANGUAGE_CODE,
                    entities=entities,
                )
                for result in results:
                    logger.debug(
                        "Result [%s] found",
                        result,
                    )
                    yield PersonalDataDetection(file_path, result, text_value=line[result.start : result.end])

    def _scan_path(
        self,
        analyzer: AnalyzerEngine,
        entities: List[str],
        file_path: str,
    ) -> Iterator[PersonalDataDetection]:
        file_extension = Path(file_path).suffix.lower()
        if file_extension in self.LINE_BY_LINE_FILE_EXTENSIONS:
            yield from self._scan_line_by_line(analyzer, entities, file_path)
        else:
            yield from self._scan_file_contents(analyzer, entities, file_path)

    def _get_paths_to_scan(
        self,
        paths: List[str],
        exclusions: List[re.Pattern[str]],
        github_action: bool = False,
    ):
        if github_action:
            repo = git.Repo("./")
            logger.debug("Scanning files in git repository %s", repo)
            paths = [entry.path for entry in repo.tree().traverse()]

        for path in paths:
            if self._should_scan_path(path, exclusions):
                yield path

    def scan(
        self,
        github_action: bool = False,
    ) -> Iterator[PersonalDataDetection]:
        analyzer = self._get_analyzer()
        entities = analyzer.get_supported_entities()
        exclusions = list(self._get_exclusions(exclusions_file=PRESIDIO_EXCLUSIONS_FILE_PATH))
        logger.debug("Exclusions file loaded with exclusions %s", exclusions)

        for path in self._get_paths_to_scan(
            self.paths,
            exclusions,
            github_action,
        ):
            yield from self._scan_path(analyzer, entities, path)
