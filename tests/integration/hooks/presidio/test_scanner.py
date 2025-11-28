import tempfile

import pytest
from src.hooks.presidio.scanner import PresidioScanner
from presidio_analyzer.predefined_recognizers.generic import PhoneRecognizer, EmailRecognizer


class TestPresidioScanner:
    def test_get_analyzer_returns_expected_recognizers(self):
        scanner = PresidioScanner()
        recognizers = scanner._get_analyzer().get_recognizers()

        assert len(recognizers) == 2
        assert recognizers[0].to_dict() == PhoneRecognizer(supported_regions=["GB"]).to_dict()
        assert recognizers[1].to_dict() == EmailRecognizer().to_dict()

    def test_scan_returns_matches_for_email_address(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = "My email is test_email@test.com"
            tf.write(contents)
            tf.seek(0)

            results = list(PresidioScanner(verbose=True, paths=[tf.name]).scan())

            assert results[0].result.entity_type == "EMAIL_ADDRESS"
            assert results[0].text_value == "test_email@test.com"

    @pytest.mark.parametrize("phone_number", (["02920000000", "07000000000"]))
    def test_scan_returns_matches_for_phone_number(self, phone_number):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = f"My phone number is {phone_number}"
            tf.write(contents)
            tf.seek(0)

            results = list(PresidioScanner(verbose=True, paths=[tf.name]).scan())

            assert results[0].result.entity_type == "PHONE_NUMBER"
            assert results[0].text_value == phone_number

    def test_scan_returns_no_matches_for_names(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = "My name is john smith"
            tf.write(contents)
            tf.seek(0)

            results = list(PresidioScanner(verbose=True, paths=[tf.name]).scan())

            assert results == []

    def test_scan_returns_no_matches_for_address(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = "I live at 10 Downing Street, SW1A 2AA, London"
            tf.write(contents)
            tf.seek(0)

            results = list(PresidioScanner(verbose=True, paths=[tf.name]).scan())

            assert results == []
