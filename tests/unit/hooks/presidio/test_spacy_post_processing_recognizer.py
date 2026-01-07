from unittest.mock import MagicMock, patch
from presidio_analyzer.predefined_recognizers.nlp_engine_recognizers import SpacyRecognizer
from src.hooks.presidio.spacy_post_processing_recognizer import SpacyPostProcessingRecognizer


class TestSpacyPostProcessingRecognizer:
    def test_entity_not_in_supported_entities_is_excluded(self):
        with patch.object(SpacyRecognizer, "analyze") as mock_analyze:
            skipped_entity = MagicMock()
            skipped_entity.entity_type = "UNKNOWN_ENTITY"
            mock_analyze.return_value = [skipped_entity]

            recognizer = SpacyPostProcessingRecognizer()

            assert recognizer.analyze("ABC", ["LOCATION"]) == []

    def test_entity_with_text_value_not_matching_regex_is_excluded(self):
        with patch.object(SpacyRecognizer, "analyze") as mock_analyze:
            skipped_entity = MagicMock()
            skipped_entity.entity_type = "LOCATION"
            skipped_entity.start = 0
            skipped_entity.end = 2

            mock_analyze.return_value = [skipped_entity]

            recognizer = SpacyPostProcessingRecognizer()

            assert recognizer.analyze("10 abc", ["LOCATION"]) == []

    def test_entity_with_text_value_matching_regex_is_included(self):
        with patch.object(SpacyRecognizer, "analyze") as mock_analyze:
            entity = MagicMock()
            entity.entity_type = "LOCATION"
            entity.start = 0
            entity.end = 3

            mock_analyze.return_value = [entity]

            recognizer = SpacyPostProcessingRecognizer()

            assert recognizer.analyze("abc", ["LOCATION"]) == [entity]
