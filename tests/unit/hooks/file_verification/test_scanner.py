import os
from unittest import mock
from anyio import NamedTemporaryFile
import pytest
from src.hooks.config import BLOCKED_FILE_EXTENSION_REGEX, MAX_FILE_SIZE_BYTES
from src.hooks.file_verification.scanner import FileVerificationScanner


class TestFileVerificationScanner:
    @pytest.mark.parametrize("file_extension", [".zip", ".pfx", ".xps", ".bak", ".xlsx"])
    def test_is_path_blocked_returns_false_for_invalid_path(self, file_extension):
        assert FileVerificationScanner()._is_path_blocked(f"file.{file_extension}", BLOCKED_FILE_EXTENSION_REGEX) is True

    @pytest.mark.parametrize("file_extension", [".py", ".js", ".ts"])
    def test_is_path_blocked_returns_none_for_valid_path(self, file_extension):
        assert FileVerificationScanner()._is_path_blocked(f"file.{file_extension}", BLOCKED_FILE_EXTENSION_REGEX) is False

    async def test_check_file_size_exceeds_maximum_adds_file_to_list_when_file_size_is_above_maximum(self):
        files = []
        async with NamedTemporaryFile(
            mode="wb",
        ) as ntf:
            await ntf.write(os.urandom(MAX_FILE_SIZE_BYTES + 1))
            await FileVerificationScanner()._check_file_size_exceeds_maximum(ntf.name, files)
            assert ntf.name in files

    async def test_check_file_size_exceeds_maximum_does_not_add_file_to_list_when_file_size_is_below_maximum(self):
        files = []
        async with NamedTemporaryFile(
            mode="wb",
        ) as ntf:
            await ntf.write(os.urandom(100))
            await FileVerificationScanner()._check_file_size_exceeds_maximum(ntf.name, files)
            assert ntf.name not in files

    async def test_get_exclusions_returns_empty_list_when_exclusions_file_is_missing(self):
        assert await FileVerificationScanner()._get_exclusions("not_present_file.txt") == []

    async def test_get_exclusions_returns_all_exclusions_in_exclusions_file(self):
        async with NamedTemporaryFile("w+t") as exclusions_file:
            await exclusions_file.writelines(["file1.txt", os.linesep, "file2.csv"])
            await exclusions_file.seek(0)

            assert await FileVerificationScanner()._get_exclusions(exclusions_file.name) == ["file1.txt", "file2.csv"]

    async def test_get_paths_to_scan_returns_same_paths_if_no_exclusions_exist(self):
        paths = ["file1.pdf", "file2.py", "file3.yml"]
        with mock.patch.object(FileVerificationScanner, "_get_exclusions", return_value=[]):
            assert await FileVerificationScanner()._get_paths_to_scan(paths) == paths

    async def test_get_paths_to_scan_returns_only_paths_not_in_the_exclusions_list(self):
        paths = ["file1.pdf", "file2.py", "file3.yml"]
        with mock.patch.object(FileVerificationScanner, "_get_exclusions", return_value=["file1.pdf"]):
            assert await FileVerificationScanner()._get_paths_to_scan(paths) == ["file2.py", "file3.yml"]

    async def test_scan_returns_result_with_blocked(self):
        def check_file_size(path, files):
            if path == "file1.txt":
                files.append(path)

        mock_is_path_blocked = mock.MagicMock()
        mock_is_path_blocked.side_effect = [False, False, True]  # block file3.xlsx

        mock_check_file_size_exceeds_maximum = mock.AsyncMock()
        mock_check_file_size_exceeds_maximum.side_effect = check_file_size

        with mock.patch.multiple(
            FileVerificationScanner,
            _is_path_blocked=mock_is_path_blocked,
            _check_file_size_exceeds_maximum=mock_check_file_size_exceeds_maximum,
        ):
            scan_result = await FileVerificationScanner(paths=["file1.txt", "file2.csv", "file3.xlsx"]).scan()

            assert scan_result.forbidden == ["file3.xlsx"]
            assert scan_result.exceeds_file_size == ["file1.txt"]
