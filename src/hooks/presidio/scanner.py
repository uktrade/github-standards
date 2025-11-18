import io

from pathlib import Path
import re
from typing import List

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from src.hooks.config import (
    DEFAULT_FILE_TYPES,
    DEFAULT_LANGUAGE_CODE,
    EXCLUSIONS_FILE_PATH,
    LOGGER,
    SPACY_ENTITIES,
    SPACY_MODEL_NAME,
)

logger = LOGGER


class Detection:
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
            "ner_model_configuration": {"labels_to_ignore": ["CARDINAL"]},
        }

        # Create NLP engine based on configuration
        provider = NlpEngineProvider(nlp_configuration=engine_configuration)
        nlp_engine = provider.create_engine()

        provider = RecognizerRegistryProvider(
            registry_configuration={
                "supported_languages": [DEFAULT_LANGUAGE_CODE],
                "recognizers": [
                    {"name": "EmailRecognizer", "type": "predefined"},
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

    def _is_path_excluded(self, path, exclusions_file):
        if not Path(exclusions_file).exists():
            logger.debug("The exclusions file %s is not present", exclusions_file)
            return False

        with io.open(exclusions_file, "r", encoding="utf-8") as file:
            for _, exclusion_regex in enumerate(file):
                try:
                    regex = re.compile(exclusion_regex)
                    match = regex.search(path)
                    if match is not None:
                        logger.info("Path %s matches regex %s and should be excluded", path, exclusion_regex)

                        return True
                    logger.debug("Path %s does not have a match in regex %s", path, exclusion_regex)
                except re.error:
                    logger.error(
                        "The regex %s in file %s could not be compiled into a valid regex", exclusion_regex, exclusions_file
                    )
                    raise
            logger.debug("The path %s was not found in any regexes in file %s", path, exclusions_file)
        return False

    def _should_process_path(self, path):
        if not Path(path).exists():
            logger.debug("Path %s does not exist", path)
            return False

        if not Path(path).is_file():
            logger.debug("Path %s is a directory, presidio can only scan files", path)
            return False

        # check against the scan-exclusions file regex
        if self._is_path_excluded(path, exclusions_file=EXCLUSIONS_FILE_PATH):
            logger.debug("Path %s is in the excluded file", path)
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

    def scan(self) -> None | List[Detection]:
        analyzer = self._get_analyzer()
        detections = []
        for path in self.paths:
            if self._should_process_path(path):
                with io.open(path, "r", encoding="utf-8") as file_contents:
                    for line_number, line in enumerate(file_contents):
                        results = analyzer.analyze(
                            text=line,
                            language=DEFAULT_LANGUAGE_CODE,
                        )
                        for result in results:
                            logger.debug("Result found in line number %s, for text %s", line_number, line)
                            detections.append(Detection(path, line_number, result))

        if detections:
            return detections

        logger.debug("All files were scanned and no personal data was found")
        return None
