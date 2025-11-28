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
    SPACY_MODEL_NAME,
)

logger = LOGGER


class PersonalDataDetection:
    def __init__(self, filename: str, line_number: float, result: RecognizerResult) -> None:
        self.filename = filename
        self.line_number = line_number
        self.result = result

    def __repr__(self) -> str:
        return f"Found possible personal data.\nFilename: {self.filename}\nLine number: {self.line_number}\nDetected entity: {self.result}"


class PresidioScanner:
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
                    # {"name": "SpacyRecognizer", "type": "predefined", "supported_entities": SPACY_ENTITIES},
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

    def _should_process_path(self, path: str):
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

    def _scan_path(
        self, analyzer: AnalyzerEngine, entities: List[str], file_path: str, exclusions: List[re.Pattern[str]]
    ) -> Iterator[PersonalDataDetection]:
        # check against the scan-exclusions file regex
        if self._is_path_excluded(file_path, exclusions):
            logger.debug("Path %s is in the excluded file", file_path)
            return

        if self._should_process_path(file_path):
            with io.open(file_path, "r", encoding="utf-8") as file_contents:
                for line_number, line in enumerate(file_contents):
                    results = analyzer.analyze(
                        text=line,
                        language=DEFAULT_LANGUAGE_CODE,
                        entities=entities,
                    )
                    for result in results:
                        logger.debug(
                            "Result [%s] found in line number %s, for text %s",
                            result,
                            line_number,
                            line,
                        )
                        yield PersonalDataDetection(file_path, line_number, result)

    def _get_paths(self, paths: List[str], github_action: bool = False):
        if not github_action:
            return paths
        repo = git.Repo("./")
        logger.debug("Scanning files in git repository %s", repo)
        return [entry.path for entry in repo.tree().traverse()]

    def scan(
        self,
        github_action: bool = False,
    ) -> Iterator[PersonalDataDetection]:
        analyzer = self._get_analyzer()
        entities = analyzer.get_supported_entities()
        exclusions = list(self._get_exclusions(exclusions_file=PRESIDIO_EXCLUSIONS_FILE_PATH))
        logger.debug("Exclusions file loaded with exclusions %s", exclusions)

        for path in self._get_paths(
            self.paths,
            github_action,
        ):
            yield from self._scan_path(analyzer, entities, path, exclusions)
