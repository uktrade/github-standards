import io

import json
from pathlib import Path
from typing import Iterator, List

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from src.hooks.config import (
    DEFAULT_LANGUAGE_CODE,
    LOGGER,
    SPACY_MODEL_NAME,
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
                    "LANGUAGE",
                    "ORDINAL",
                    "PERCENT",
                    "LAW",
                ],
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
                    # Remove spacy for now, as it has a lot of false positives
                    # {"name": "SpacyRecognizer", "type": "predefined", "supported_entities": SPACY_ENTITIES},
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
