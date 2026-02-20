import pytest
import src.hooks.presidio.scanner as scanner

from random import randint
from anyio import NamedTemporaryFile, TemporaryDirectory
from tempfile import NamedTemporaryFile as NamedTemporaryFileSync
from unittest.mock import patch

from presidio_analyzer import Pattern, PatternRecognizer
from src.hooks.presidio.path_filter import PathFilter
from src.hooks.presidio.scanner import PresidioScanner
from presidio_analyzer.predefined_recognizers.generic import PhoneRecognizer, EmailRecognizer


class TestPresidioScanner:
    def test_get_analyzer_returns_expected_recognizers(self):
        scanner = PresidioScanner()
        recognizers = scanner._get_analyzer().get_recognizers()

        assert len(recognizers) == 3
        recognizers.sort(key=lambda x: x.name)

        assert recognizers[0].to_dict() == EmailRecognizer().to_dict()
        assert recognizers[1].to_dict() == PhoneRecognizer(supported_regions=["GB"]).to_dict()
        assert (
            recognizers[2].to_dict()
            == PatternRecognizer(
                name="UKPostcodeRecognizer",
                supported_entity="UK_POSTCODE",
                patterns=[
                    Pattern(
                        "postcode (Medium)",
                        "(?:^|\\s|\\'|\"|\\=|\\,)([A-Z][A-HJ-Y]?\\d[A-Z\\d]? ?\\d[A-Z]{2}|GIR ?0A{2})(?:$|\\s|\\'|\"|\\,|\\.)",
                        0.5,
                    )
                ],
                context=["postcode", "address", "postal code"],
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

            assert results.paths_containing_personal_data[0].results[0].result.entity_type == "EMAIL_ADDRESS"
            assert results.paths_containing_personal_data[0].results[0].text_value == "test_email@test.com"

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

            assert results.paths_containing_personal_data[0].results[0].result.entity_type == "PHONE_NUMBER"
            assert results.paths_containing_personal_data[0].results[0].text_value == phone_number

    @pytest.mark.parametrize(
        "postcode_str,expected_match",
        [
            ("My postcode is sw1A 1Aa", " sw1A 1Aa"),
            ("My postcode is sw1A 1Aa and my city is London", " sw1A 1Aa "),
            ("I live at the address Cf10 1eP", " Cf10 1eP"),
            ("Cf101eP", "Cf101eP"),
            ("=Cf101eP", "=Cf101eP"),
            (",Cf101eP", ",Cf101eP"),
            ("ABC DEF d832fe.", " d832fe."),
            ("ABC DEF d832fe,", " d832fe,"),
        ],
    )
    async def test_scan_returns_matches_for_postcode(self, postcode_str, expected_match):
        async with NamedTemporaryFile(
            mode="w+t",
            suffix=".txt",
        ) as tf:
            with (
                patch.object(PathFilter, "_get_exclusions") as mock_exclusions,
            ):
                mock_exclusions.return_value = []
                await tf.write(postcode_str)
                await tf.seek(0)

                results = await PresidioScanner(verbose=True, paths=[tf.name]).scan()

                assert results.paths_containing_personal_data[0].results[0].result.entity_type == "UK_POSTCODE"
                assert results.paths_containing_personal_data[0].results[0].text_value == expected_match

    async def test_scan_returns_no_matches_for_names(self):
        async with NamedTemporaryFile(
            mode="w+t",
            suffix=".txt",
        ) as tf:
            contents = "My name is john smith"
            await tf.write(contents)
            await tf.seek(0)

            results = await PresidioScanner(verbose=True, paths=[tf.name]).scan()

            assert len(results.paths_containing_personal_data) == 0
            assert len(results.paths_without_personal_data) == 1

    @pytest.mark.parametrize(
        "file",
        (
            [
                "tests/test_data/personal_data.csv",
                "tests/test_data/personal_data.txt",
                "tests/test_data/personal_data.yaml",
                "tests/test_data/personal_data.yml",
                "tests/test_data/personal_data.py",
            ]
        ),
    )
    async def test_scan_path_with_test_file_containing_personal_data_returns_at_least_one_match(self, file):
        with patch.object(PathFilter, "_get_exclusions") as mock_exclusions:
            mock_exclusions.return_value = []
            results = await PresidioScanner(verbose=True, paths=[file]).scan()

            assert len(results.paths_containing_personal_data) > 0
            assert len(results.paths_without_personal_data) == 0

    async def test_scan_for_files_with_each_path_status_returns_expected_results(self):
        async with TemporaryDirectory(delete=True) as td:
            files_to_skip = [
                NamedTemporaryFileSync(
                    dir=td,
                    suffix=".jpg",
                    mode="w+t",
                    prefix=f"SKIPPED_FILE_{i}_",
                )
                for i in range(10, randint(15, 30))
            ]

            files_to_exclude = [
                NamedTemporaryFileSync(
                    dir=td,
                    suffix=".txt",
                    mode="w+t",
                    prefix=f"EXCLUDED_FILE_{i}_",
                )
                for i in range(10, randint(15, 30))
            ]
            exclude_file = NamedTemporaryFileSync(dir=td, mode="w+t")
            exclude_file.writelines(f"{exclude_file.name}\r" for exclude_file in files_to_exclude)
            exclude_file.seek(0)

            files_to_with_no_personal_data = [
                NamedTemporaryFileSync(
                    dir=td,
                    suffix=".txt",
                    mode="w+t",
                    prefix=f"NO_PERSONAL_DATA_FILE_{i}_",
                )
                for i in range(10, randint(15, 30))
            ]

            all_files = files_to_skip + files_to_exclude + files_to_with_no_personal_data

            with patch.object(scanner, "PRESIDIO_EXCLUSIONS_FILE_PATH", exclude_file.name):
                paths = [file.name for file in all_files]
                scan_result = await PresidioScanner(verbose=True, paths=paths).scan()
                assert {result.path for result in scan_result.paths_excluded} == {file.name for file in files_to_exclude}
                assert {result.path for result in scan_result.paths_skipped} == {file.name for file in files_to_skip}
                assert {result.path for result in scan_result.paths_without_personal_data} == {
                    file.name for file in files_to_with_no_personal_data
                }
