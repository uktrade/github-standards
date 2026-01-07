import os
import pytest
import re
import tempfile

from anyio import Path

from src.hooks.presidio.path_filter import PathFilter, PathScanStatus
from unittest.mock import patch


class TestPathFilter:
    def test_is_path_excluded_returns_true_when_path_is_excluded(self):
        with tempfile.NamedTemporaryFile("w+t") as tf:
            exclusions = [re.compile(tf.name)]
            assert PathFilter()._is_path_excluded(tf.name, exclusions) is True

    def test_is_path_excluded_returns_false_when_path_is_not_excluded(self):
        with tempfile.NamedTemporaryFile("w+t") as tf:
            exclusions = [re.compile(tf.name)]
            assert PathFilter()._is_path_excluded("/a.txt", exclusions) is False

    async def test_check_is_path_invalid_returns_excluded_status_when_path_is_excluded(self):
        with patch.object(PathFilter, "_is_path_excluded", return_value=True):
            assert await PathFilter()._check_is_path_invalid("/not_real", []) is PathScanStatus.EXCLUDED

    async def test_check_is_path_invalid_returns_skipped_status_when_path_does_not_exist(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = False
            assert await PathFilter()._check_is_path_invalid("/not_real", []) is PathScanStatus.SKIPPED

    async def test_check_is_path_invalid_returns_skipped_status_when_path_is_a_directory(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = False
            assert await PathFilter()._check_is_path_invalid("/a", []) is PathScanStatus.SKIPPED

    async def test_check_is_path_invalid_returns_skipped_status_when_path_is_not_accepted_file_extension(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert await PathFilter()._check_is_path_invalid("a.png", []) is PathScanStatus.SKIPPED

    @pytest.mark.parametrize("file_extension", [".txt", ".yml", ".yaml", ".csv"])
    async def test_check_is_path_invalid_returns_none_when_path_is_an_accepted_file_extension(self, file_extension):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "is_file") as mock_is_file,
            patch.object(PathFilter, "_is_path_excluded", return_value=False),
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            assert await PathFilter()._check_is_path_invalid(f"a{file_extension}", []) is None

    async def test_get_exclusions_returns_empty_list_when_exclusions_file_is_missing(self):
        assert await PathFilter()._get_exclusions("not_present_file.txt") == []

    async def test_get_exclusions_throws_error_when_regex_does_not_compile(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file, pytest.raises(re.error):
            exclusions_file.write("folder/**")
            exclusions_file.seek(0)
            await PathFilter()._get_exclusions(exclusions_file.name)

    async def test_get_exclusions_returns_all_regexes_in_exclusions_file(self):
        with tempfile.NamedTemporaryFile("w+t") as exclusions_file:
            exclusions_file.writelines(["folder1/*", os.linesep, "folder2/*"])
            exclusions_file.seek(0)
            assert await PathFilter()._get_exclusions(exclusions_file.name) == [
                re.compile("folder1/*"),
                re.compile("folder2/*"),
            ]
