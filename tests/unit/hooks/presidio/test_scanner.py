import pytest
import re
import tempfile

from pathlib import Path

from src.hooks.presidio.scanner import PresidioScanner
from unittest.mock import patch


class TestPresidioScanner:
    def test_should_process_path_returns_false_when_path_does_not_exist(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            assert PresidioScanner()._should_process_path("/not_real") is False

    def test_should_process_path_returns_false_when_path_is_a_directory(self):
        with patch.object(Path, "exists") as mock_exists, patch.object(Path, "is_file") as mock_is_file:
            mock_exists.return_value = True
            mock_is_file.return_value = False
            assert PresidioScanner()._should_process_path("/a") is False

    def test_should_process_path_returns_false_when_path_is_excluded(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PresidioScanner, "_is_path_excluded") as mock_is_path_excluded,
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            mock_is_path_excluded.return_value = True
            assert PresidioScanner()._should_process_path("/a") is False

    def test_should_process_path_returns_true_when_path_is_not_excluded(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PresidioScanner, "_is_path_excluded") as mock_is_path_excluded,
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            mock_is_path_excluded.return_value = False
            assert PresidioScanner()._should_process_path("/a.txt") is True

    def test_should_process_path_returns_false_when_path_is_not_accepted_file_extension(self):
        with patch.object(Path, "exists") as mock_exists, patch.object(Path, "is_file") as mock_is_file:
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert PresidioScanner()._should_process_path("a.png") is False

    @pytest.mark.parametrize("file_extension", [".txt", ".yml", ".yaml", ".csv"])
    def test_should_process_path_returns_true_when_path_is_an_accepted_file_extension(self, file_extension):
        with patch.object(Path, "exists") as mock_exists, patch.object(Path, "is_file") as mock_is_file:
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert PresidioScanner()._should_process_path(f"a{file_extension}") is True

    def test_is_path_excluded_returns_false_when_exclusions_file_is_missing(self):
        assert PresidioScanner()._is_path_excluded("a.txt", "not_present_file.txt") is False

    def test_is_path_excluded_throws_error_when_regex_does_not_compile(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file, pytest.raises(re.error):
            exclusions_file.write("folder/**")
            exclusions_file.seek(0)
            assert PresidioScanner()._is_path_excluded("a.txt", exclusions_file.name) is False

    def test_is_path_excluded_returns_false_when_path_does_not_match_entry_in_exclusions_file(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file:
            exclusions_file.write("folder/*")
            exclusions_file.seek(0)
            assert PresidioScanner()._is_path_excluded("a.txt", exclusions_file.name) is False

    def test_is_path_excluded_returns_true_when_path_matches_entry_in_exclusions_file(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file, tempfile.NamedTemporaryFile("w+t") as scanned_file:
            exclusions_file.write(scanned_file.name)
            exclusions_file.seek(0)
            assert PresidioScanner()._is_path_excluded(scanned_file.name, exclusions_file.name) is True

    def test_scan_with_no_paths_returns_no_error_response(self):
        assert PresidioScanner().scan() is None

    def test_scan_with_a_file_with_no_personal_data_returns_no_error_response(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt") as tf,
            patch.object(PresidioScanner, "_get_analyzer"),
        ):
            tf.write(b"No personal data here")
            tf.seek(0)
            assert PresidioScanner(paths=[tf.name]).scan() is None

    def test_scan_with_a_file_containing_personal_data_returns_no_error_response(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt") as tf,
        ):
            tf.write(b"My name is John Smith. \nMy email is john.smith@test.com")
            tf.seek(0)

            result = PresidioScanner(paths=[tf.name]).scan()

            assert result is not None
            assert len(result) == 2
