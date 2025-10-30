import logging
import os

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider

from src.hooks.hooks_base import Hook, HookRunResult

logger = logging.getLogger()


class RunPIIScan(Hook):
    def validate_args(self) -> bool:
        return True

    def _validate_hook_settings(self, dbt_repo_config) -> bool:
        return True

    def run(self) -> HookRunResult:
        # Set up the engine, loads the NLP module (spaCy model by default)
        # and other PII recognizers
        # Create configuration containing engine name and models
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_sm"},
            ],
        }

        # Create NLP engine based on configuration
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        provider = RecognizerRegistryProvider(conf_file="./recognizers-config.yml")

        analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine, supported_languages=["en"], registry=provider.create_recognizer_registry()
        )
        logger.debug("analyzer: %s", analyzer)
        logger.debug("cwd: %s", os.getcwd())

        analyzer.analyze(text="His name is Mr. Jones and his phone number is 212-555-5555", language="en")

        return HookRunResult(True)
