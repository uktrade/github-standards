import pytest

from anyio import NamedTemporaryFile
from unittest.mock import patch

from presidio_analyzer import Pattern, PatternRecognizer
from src.hooks.presidio.path_filter import PathFilter
from src.hooks.presidio.scanner import PresidioScanner
from presidio_analyzer.predefined_recognizers.generic import PhoneRecognizer, EmailRecognizer

from src.hooks.presidio.spacy_post_processing_recognizer import SpacyPostProcessingRecognizer


class TestPresidioScanner:
    def test_get_analyzer_returns_expected_recognizers(self):
        scanner = PresidioScanner()
        recognizers = scanner._get_analyzer().get_recognizers()

        assert len(recognizers) == 4
        recognizers.sort(key=lambda x: x.name)

        assert recognizers[0].to_dict() == EmailRecognizer().to_dict()
        assert recognizers[1].to_dict() == PhoneRecognizer(supported_regions=["GB"]).to_dict()
        assert recognizers[2].to_dict() == SpacyPostProcessingRecognizer(supported_entities=["PERSON", "LOCATION"]).to_dict()
        assert (
            recognizers[3].to_dict()
            == PatternRecognizer(
                name="UKPostcodeRecognizer",
                supported_entity="UK_POSTCODE",
                patterns=[Pattern("postcode (Medium)", r"([A-Z][A-HJ-Y]?\d[A-Z\d]? ?\d[A-Z]{2}|GIR ?0A{2})$", 0.5)],
                context=["postcode", "address"],
            ).to_dict()
        )

    async def test_scan_returns_matches_for_email_address(self):
        async with NamedTemporaryFile(
            mode="w+t",
            suffix=".txt",
        ) as tf:
            contents = "My email is test_email@test.com"

            await tf.write(contents)
            await tf.seek(0)

            results = await PresidioScanner(verbose=True, paths=[tf.name]).scan()

            assert results.invalid_path_scans[0].results[0].result.entity_type == "EMAIL_ADDRESS"
            assert results.invalid_path_scans[0].results[0].text_value == "test_email@test.com"

    @pytest.mark.parametrize("phone_number", (["02920000000", "07000000000"]))
    async def test_scan_returns_matches_for_phone_number(self, phone_number):
        async with NamedTemporaryFile(
            mode="w+t",
            suffix=".txt",
        ) as tf:
            contents = f"My phone number is {phone_number}"
            await tf.write(contents)
            await tf.seek(0)

            results = await PresidioScanner(verbose=True, paths=[tf.name]).scan()

            assert results.invalid_path_scans[0].results[0].result.entity_type == "PHONE_NUMBER"
            assert results.invalid_path_scans[0].results[0].text_value == phone_number

    @pytest.mark.parametrize("postcode", (["SW1A 1AA", "CF10 4PD"]))
    async def test_scan_returns_matches_for_postcode(self, postcode):
        async with NamedTemporaryFile(
            mode="w+t",
            suffix=".txt",
        ) as tf:
            with (
                patch.object(PathFilter, "_get_exclusions") as mock_exclusions,
            ):
                mock_exclusions.return_value = []
                contents = f"My postcode is {postcode}"
                await tf.write(contents)
                await tf.seek(0)

                results = await PresidioScanner(verbose=True, paths=[tf.name]).scan()

                assert results.invalid_path_scans[0].results[0].result.entity_type == "UK_POSTCODE"
                assert results.invalid_path_scans[0].results[0].text_value == postcode

    async def test_scan_returns_no_matches_for_names(self):
        async with NamedTemporaryFile(
            mode="w+t",
            suffix=".txt",
        ) as tf:
            contents = "My name is john smith"
            await tf.write(contents)
            await tf.seek(0)

            results = await PresidioScanner(verbose=True, paths=[tf.name]).scan()

            assert len(results.invalid_path_scans) == 0
            assert len(results.valid_path_scans) == 1

    async def test_scan_returns_matches_for_location(self):
        async with NamedTemporaryFile(
            mode="w+t",
            suffix=".txt",
        ) as tf:
            contents = "I live at 10 Downing Street, London"
            await tf.write(contents)
            await tf.seek(0)

            results = await PresidioScanner(verbose=True, paths=[tf.name]).scan()

            assert len(results.invalid_path_scans) == 1
            assert len(results.valid_path_scans) == 0

    @pytest.mark.parametrize(
        "file",
        (
            [
                "tests/test_data/personal_data.csv",
                "tests/test_data/personal_data.txt",
                "tests/test_data/personal_data.yaml",
                "tests/test_data/personal_data.yml",
            ]
        ),
    )
    async def test_scan_path_with_test_file_containing_personal_data_returns_at_least_one_match(self, file):
        with patch.object(PathFilter, "_get_exclusions") as mock_exclusions:
            mock_exclusions.return_value = []
            results = await PresidioScanner(verbose=True, paths=[file]).scan()

            assert len(results.invalid_path_scans) > 0
            assert len(results.valid_path_scans) == 0
