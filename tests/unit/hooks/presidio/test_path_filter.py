import os
import pytest
import re
import tempfile

from pathlib import Path

from src.hooks.presidio.path_filter import PathFilter
from unittest.mock import MagicMock, patch


class TestPathFilter:
    def test_is_path_excluded_returns_true_when_path_is_excluded(self):
        with tempfile.NamedTemporaryFile("w+t") as tf:
            exclusions = [re.compile(tf.name)]
            assert PathFilter()._is_path_excluded(tf.name, exclusions) is True

    def test_is_path_excluded_returns_false_when_path_is_not_excluded(self):
        with tempfile.NamedTemporaryFile("w+t") as tf:
            exclusions = [re.compile(tf.name)]
            assert PathFilter()._is_path_excluded("/a.txt", exclusions) is False

    def test_should_scan_path_returns_false_when_path_is_excluded(self):
        with patch.object(PathFilter, "_is_path_excluded", return_value=True):
            assert PathFilter()._should_scan_path("/not_real", []) is False

    def test_should_scan_path_returns_false_when_path_does_not_exist(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = False
            assert PathFilter()._should_scan_path("/not_real", []) is False

    def test_should_scan_path_returns_false_when_path_is_a_directory(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = False
            assert PathFilter()._should_scan_path("/a", []) is False

    def test_should_scan_path_returns_false_when_path_is_not_accepted_file_extension(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert PathFilter()._should_scan_path("a.png", []) is False

    @pytest.mark.parametrize("file_extension", [".txt", ".yml", ".yaml", ".csv"])
    def test_should_scan_path_returns_true_when_path_is_an_accepted_file_extension(self, file_extension):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert PathFilter()._should_scan_path(f"a{file_extension}", []) is True

    def test_get_exclusions_returns_empty_list_when_exclusions_file_is_missing(self):
        assert list(PathFilter()._get_exclusions("not_present_file.txt")) == []

    def test_get_exclusions_throws_error_when_regex_does_not_compile(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file, pytest.raises(re.error):
            exclusions_file.write("folder/**")
            exclusions_file.seek(0)
            list(PathFilter()._get_exclusions(exclusions_file.name))

    def test_get_exclusions_returns_all_regexes_in_exclusions_file(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file:
            exclusions_file.writelines(["folder1/*", os.linesep, "folder2/*"])
            exclusions_file.seek(0)
            assert list(PathFilter()._get_exclusions(exclusions_file.name)) == [
                re.compile("folder1/*"),
                re.compile("folder2/*"),
            ]

    def test_get_paths_to_scan_returns_same_list_when_not_running_as_github_action(self):
        files = ["1.txt", "2.json"]
        with patch.object(PathFilter, "_should_scan_path", return_value=True):
            assert list(PathFilter().get_paths_to_scan(files)) == files

    def test_get_paths_to_scan_only_returns_files_that_should_be_scanned(self):
        files = ["1.txt", "2.json"]
        with patch.object(PathFilter, "_should_scan_path") as mock_should_scan_path:
            mock_should_scan_path.side_effect = [True, False]
            assert list(PathFilter().get_paths_to_scan(files)) == [files[0]]

    def test_get_paths_to_scan_returns_list_of_git_files_when_running_as_github_action(self):
        with (
            patch("src.hooks.presidio.path_filter.git.Repo") as mock_repo,
            patch.object(PathFilter, "_should_scan_path", return_value=True),
        ):
            git_file_1 = MagicMock()
            git_file_1.path = "1.rt"

            mock_repo.return_value.tree.return_value.traverse.return_value = [git_file_1]

            assert list(PathFilter().get_paths_to_scan(["1.txt", "2.json"], github_action=True)) == [git_file_1.path]
