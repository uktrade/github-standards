import logging
import re

from typing import List, Set, Tuple

from presidio_analyzer.predefined_recognizers.nlp_engine_recognizers import SpacyRecognizer

logger = logging.getLogger("presidio-analyzer")


class SpacyPostProcessingRecognizer(SpacyRecognizer):
    """

    Spacy returns names and locations with special symbols, which are false positives. This post processing
    recognizer filters spacy results to only include results that are contain letters or spaces

    """

    CHARS_AND_SPACES_REGEX = r"^(?=.*[a-zA-Z])[a-zA-Z\s]+$"
    ENTITIES = ["LOCATION"]

    def __init__(
        self,
        supported_language: str = "en",
        supported_entities: List[str] | None = None,
        ner_strength: float = 0.85,
        default_explanation: str | None = None,
        check_label_groups: List[Tuple[Set, Set]] | None = None,
        context: List[str] | None = None,
    ):
        super().__init__(
            supported_language,
            supported_entities if not supported_entities else self.ENTITIES,
            ner_strength,
            default_explanation,
            check_label_groups,
            context,
        )

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None):
        results = super().analyze(text=text, entities=entities, nlp_artifacts=nlp_artifacts)
        filtered_results = []

        for result in results:
            if result.entity_type in self.supported_entities:
                text = text[result.start : result.end]
                is_valid = re.search(self.CHARS_AND_SPACES_REGEX, text, re.IGNORECASE)
                if is_valid:
                    filtered_results.append(result)
                else:
                    logger.debug("Text value %s did not pass regex check", text)
        return filtered_results
