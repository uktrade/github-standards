import io

from pathlib import Path
from typing import Iterator, List

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from src.hooks.config import (
    DEFAULT_LANGUAGE_CODE,
    LOGGER,
    SPACY_ENTITIES,
    SPACY_MODEL_NAME,
)
from src.hooks.presidio.path_filter import PathFilter

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
            "ner_model_configuration": {
                "labels_to_ignore": [
                    "CARDINAL",
                    "MONEY",
                    "WORK_OF_ART",
                    "FAC",
                    "PRODUCT",
                    "EVENT",
                ]
            },
        }

        # Create NLP engine based on configuration
        provider = NlpEngineProvider(nlp_configuration=engine_configuration)
        nlp_engine = provider.create_engine()

        provider = RecognizerRegistryProvider(
            registry_configuration={
                "supported_languages": [DEFAULT_LANGUAGE_CODE],
                "recognizers": [
                    {"name": "EmailRecognizer", "type": "predefined"},
                    {"name": "PhoneRecognizer", "type": "predefined", "supported_regions": ["GB"]},
                    {"name": "SpacyRecognizer", "type": "predefined", "supported_entities": SPACY_ENTITIES},
                ],
            },
        )

        registry = provider.create_recognizer_registry()

        analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=[DEFAULT_LANGUAGE_CODE],
            registry=registry,
        )

        return analyzer

    def _scan_file_contents(
        self,
        analyzer: AnalyzerEngine,
        entities: List[str],
        file_path: str,
    ):
        logger.debug("Scanning file %s contents", file_path)
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
        logger.debug("Scanning file %s line by line", file_path)
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

    def scan(
        self,
        github_action: bool = False,
    ) -> Iterator[PersonalDataDetection]:
        sources = PathFilter(self.verbose)

        analyzer = self._get_analyzer()
        entities = analyzer.get_supported_entities()

        for path in sources.get_paths_to_scan(self.paths, github_action):
            yield from self._scan_path(analyzer, entities, path)
