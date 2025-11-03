import io
import logging

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from src.hooks.hooks_base import Hook, HookRunResult

logger = logging.getLogger()


class RunPersonalDataScan(Hook):
    def validate_args(self) -> bool:
        if self.files is None or len(self.files) == 0:
            logger.debug("No files passed to hook, this hook needs at least 1 file")
            return False

        return True

    def _validate_hook_settings(self, dbt_repo_config) -> bool:
        return True

    def _get_analyzer(self) -> AnalyzerEngine:
        # Set up the engine, loads the NLP module (spaCy model by default)
        # and other PII recognizers
        # Create configuration containing engine name and models
        engine_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_sm"},
            ],
        }

        # Create NLP engine based on configuration
        provider = NlpEngineProvider(nlp_configuration=engine_configuration)
        nlp_engine = provider.create_engine()

        provider = RecognizerRegistryProvider(conf_file="./recognizers-config.yml")

        analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["en"],
            registry=provider.create_recognizer_registry(),
        )
        logger.debug("analyzer: %s", analyzer)

        return analyzer

    def run(self) -> HookRunResult:
        class Detection:
            def __init__(self, filename: str, line_number: float, result: RecognizerResult) -> None:
                self.filename = filename
                self.line_number = line_number
                self.result = result

            def __repr__(self) -> str:
                return f"Filename: {self.filename}. Line number: {self.line_number}. Detected entity: [{self.result}]"

        analyzer = self._get_analyzer()
        detections = []
        for file in self.files:
            with io.open(file, "r+") as file_contents:
                for line_number, line in enumerate(file_contents):
                    results = analyzer.analyze(
                        text=line,
                        language="en",
                        return_decision_process=True,
                    )
                    if results:
                        logger.debug("Results found potential personal data: %s", results)
                        for result in results:
                            logger.debug(">>>Result found in line number %s, for text %s", line_number, line)
                            detections.append(Detection(file, line_number, result))
        if detections:
            logger.debug("Found %s", detections)
            return HookRunResult(False)
        return HookRunResult(True)
