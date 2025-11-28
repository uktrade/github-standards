import os
import pickle
from presidio_analyzer import RecognizerResult
import pytest
import re
import tempfile

from pathlib import Path

from src.hooks.presidio.scanner import PersonalDataDetection, PresidioScanner
from unittest.mock import MagicMock, patch


class TestPresidioScanner:
    def test_is_path_excluded_returns_true_when_path_is_excluded(self):
        with tempfile.NamedTemporaryFile("w+t") as tf:
            exclusions = [re.compile(tf.name)]
            assert PresidioScanner()._is_path_excluded(tf.name, exclusions) is True

    def test_is_path_excluded_returns_false_when_path_is_not_excluded(self):
        with tempfile.NamedTemporaryFile("w+t") as tf:
            exclusions = [re.compile(tf.name)]
            assert PresidioScanner()._is_path_excluded("/a.txt", exclusions) is False

    def test_should_scan_path_returns_false_when_path_is_excluded(self):
        with patch.object(PresidioScanner, "_is_path_excluded", return_value=True):
            assert PresidioScanner()._should_scan_path("/not_real", []) is False

    def test_should_scan_path_returns_false_when_path_does_not_exist(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(PresidioScanner, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = False
            assert PresidioScanner()._should_scan_path("/not_real", []) is False

    def test_should_scan_path_returns_false_when_path_is_a_directory(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PresidioScanner, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = False
            assert PresidioScanner()._should_scan_path("/a", []) is False

    def test_should_scan_path_returns_false_when_path_is_not_accepted_file_extension(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PresidioScanner, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert PresidioScanner()._should_scan_path("a.png", []) is False

    @pytest.mark.parametrize("file_extension", [".txt", ".yml", ".yaml", ".csv"])
    def test_should_scan_path_returns_true_when_path_is_an_accepted_file_extension(self, file_extension):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PresidioScanner, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert PresidioScanner()._should_scan_path(f"a{file_extension}", []) is True

    def test_get_exclusions_returns_empty_list_when_exclusions_file_is_missing(self):
        assert list(PresidioScanner()._get_exclusions("not_present_file.txt")) == []

    def test_get_exclusions_throws_error_when_regex_does_not_compile(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file, pytest.raises(re.error):
            exclusions_file.write("folder/**")
            exclusions_file.seek(0)
            list(PresidioScanner()._get_exclusions(exclusions_file.name))

    def test_get_exclusions_returns_all_regexes_in_exclusions_file(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file:
            exclusions_file.writelines(["folder1/*", os.linesep, "folder2/*"])
            exclusions_file.seek(0)
            assert list(PresidioScanner()._get_exclusions(exclusions_file.name)) == [
                re.compile("folder1/*"),
                re.compile("folder2/*"),
            ]

    @pytest.mark.parametrize("file_extension", [".csv"])
    def test_scan_path_scans_line_by_line_for_file_extensions(self, file_extension):
        with patch.object(PresidioScanner, "_scan_line_by_line") as mock_scan_line_by_line:
            list(PresidioScanner()._scan_path(MagicMock(), [], f"file1{file_extension}"))
            mock_scan_line_by_line.assert_called()

    @pytest.mark.parametrize("file_extension", [".txt", ".yaml"])
    def test_scan_path_scans_file_contents_for_file_extensions(self, file_extension):
        with patch.object(PresidioScanner, "_scan_file_contents") as mock__scan_file_contents:
            list(PresidioScanner()._scan_path(MagicMock(), [], f"file1{file_extension}"))
            mock__scan_file_contents.assert_called()

    def test_scan_line_by_line_returns_detections_list_when_path_has_personal_data(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = "I have personal data"
            tf.write(contents)
            tf.seek(0)

            recognizer_results = [RecognizerResult("EMAIL", 0, 100, 1.0), RecognizerResult("PERSON", 0, 100, 0.9)]
            expected_scan_results = [PersonalDataDetection(tf.name, f, contents) for f in recognizer_results]

            mock_analyzer = MagicMock()
            mock_analyzer.analyze.return_value = recognizer_results

            detections = list(PresidioScanner()._scan_line_by_line(mock_analyzer, [], tf.name))

            assert pickle.dumps(detections) == pickle.dumps(expected_scan_results)

    def test_scan_file_contents_returns_detections_list_when_path_has_personal_data(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = "I have personal data"
            tf.write(contents)
            tf.seek(0)

            recognizer_results = [RecognizerResult("EMAIL", 0, 100, 1.0), RecognizerResult("PERSON", 0, 100, 0.9)]
            expected_scan_results = [PersonalDataDetection(tf.name, f, contents) for f in recognizer_results]

            mock_analyzer = MagicMock()
            mock_analyzer.analyze.return_value = recognizer_results

            detections = list(PresidioScanner()._scan_file_contents(mock_analyzer, [], tf.name))

            assert pickle.dumps(detections) == pickle.dumps(expected_scan_results)

    def test_get_paths_to_scan_returns_same_list_when_not_running_as_github_action(self):
        files = ["1.txt", "2.json"]
        with patch.object(PresidioScanner, "_should_scan_path", return_value=True):
            assert list(PresidioScanner()._get_paths_to_scan(files, [])) == files

    def test_get_paths_to_scan_only_returns_files_that_should_be_scanned(self):
        files = ["1.txt", "2.json"]
        with patch.object(PresidioScanner, "_should_scan_path") as mock_should_scan_path:
            mock_should_scan_path.side_effect = [True, False]
            assert list(PresidioScanner()._get_paths_to_scan(files, [])) == [files[0]]

    def test_get_paths_to_scan_returns_list_of_git_files_when_running_as_github_action(self):
        with (
            patch("src.hooks.presidio.scanner.git.Repo") as mock_repo,
            patch.object(PresidioScanner, "_should_scan_path", return_value=True),
        ):
            git_file_1 = MagicMock()
            git_file_1.path = "1.rt"

            mock_repo.return_value.tree.return_value.traverse.return_value = [git_file_1]

            assert list(PresidioScanner()._get_paths_to_scan(["1.txt", "2.json"], [], github_action=True)) == [
                git_file_1.path
            ]

    def test_scan_with_no_paths_returns_empty_detections_list(self):
        assert list(PresidioScanner().scan()) == []

    def test_scan_with_files_with_no_personal_data_returns_empty_detections_list(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt") as tf1,
            tempfile.NamedTemporaryFile(suffix=".csv") as tf2,
            patch.object(PresidioScanner, "_get_analyzer"),
            patch.object(PresidioScanner, "_scan_path"),
        ):
            tf1.write(b"No personal data here")
            tf1.seek(0)

            tf2.write(b"No personal data here")
            tf2.seek(0)

            assert list(PresidioScanner(paths=[tf1.name, tf2.name]).scan()) == []

    def test_scan_with_a_file_containing_personal_data_returns_no_error_response(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt") as tf,
            patch.object(PresidioScanner, "_get_analyzer"),
            patch.object(PresidioScanner, "_scan_path") as mock_scan_path,
        ):
            tf.write(b"My email is john.smith@test.com")
            tf.seek(0)

            mock_scan_path.return_value = iter([PersonalDataDetection(tf.name, MagicMock())])

            result = list(PresidioScanner(paths=[tf.name]).scan())

            assert result is not None
            assert len(result) == 1
            assert result[0].filename == tf.name
