import os
from random import randint
import tempfile
from typing import List
from anyio import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import patch


from src.hooks.cli import main_async, main
from src.hooks.config import MAX_FILE_SIZE_BYTES, PERSONAL_DATA_SCAN, TRUFFLEHOG_ERROR_CODE


class TestCLI:
    def test_run_main_with_secret_data_and_personal_data_returns_sys_exit(self):
        with (
            tempfile.TemporaryDirectory() as root_td,
            tempfile.NamedTemporaryFile(dir=root_td, mode="w+", prefix="has_personal_data_", suffix=".txt") as root_file,
            patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process,
        ):
            root_file.write("My name is John Smith")
            root_file.write("My email is john.smith@test.com")
            root_file.seek(0)

            # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
            mock_run_process.return_value.stdout = "Found keys".encode()
            mock_run_process.return_value.stderr = "Called the scanning tool and keys were found".encode()
            mock_run_process.return_value.returncode = TRUFFLEHOG_ERROR_CODE

            assert main(["run_scan", "-v", root_td]) == 1

    async def test_run_scan_with_secret_data(self):
        async with (
            TemporaryDirectory(prefix="root_dir_") as root_td,
            TemporaryDirectory(dir=root_td, prefix="sub_dir_1_") as sub_td,
            NamedTemporaryFile(dir=root_td, mode="w+", prefix="has_personal_data_", suffix=".txt") as root_file,
            NamedTemporaryFile(dir=sub_td, mode="w+", prefix="empty_file_", suffix=".txt"),
            NamedTemporaryFile(dir=sub_td, mode="w+", prefix="no_personal_data", suffix=".txt") as dir_file2,
        ):
            with patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process:
                await root_file.write("My name is John Smith")
                await root_file.write("My email is john.smith@test.com")
                await root_file.seek(0)

                await dir_file2.write("Nothing to see here")
                await dir_file2.seek(0)

                # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
                mock_run_process.return_value.stdout = "Found keys".encode()
                mock_run_process.return_value.stderr = "Called the scanning tool and keys were found".encode()
                mock_run_process.return_value.returncode = TRUFFLEHOG_ERROR_CODE

                result = await main_async(["run_scan", "-v", root_td])

                assert result == 1
                mock_run_process.assert_called()

    async def test_run_scan_with_personal_data(self):
        async with (
            TemporaryDirectory(prefix="root_dir_") as root_td,
            TemporaryDirectory(dir=root_td, prefix="sub_dir_1_") as sub_td,
            NamedTemporaryFile(dir=root_td, mode="w+", prefix="has_personal_data_", suffix=".txt") as root_file,
            NamedTemporaryFile(dir=sub_td, mode="w+", prefix="empty_file_", suffix=".txt"),
            NamedTemporaryFile(dir=sub_td, mode="w+", prefix="no_personal_data", suffix=".txt") as dir_file2,
        ):
            with patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process:
                await root_file.write("My name is John Smith")
                await root_file.write("My email is john.smith@test.com")
                await root_file.seek(0)

                await dir_file2.write("Nothing to see here")
                await dir_file2.seek(0)

                # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
                mock_run_process.return_value.stdout = "".encode()
                mock_run_process.return_value.returncode = 0

                result = await main_async(["run_scan", "-v", root_file.name])

                assert result == 1
                mock_run_process.assert_called()

    async def test_run_scan_with_large_files(self):
        async with (
            TemporaryDirectory() as root_td,
        ):
            with patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process:
                large_files: List[str] = []
                for _ in range(0, randint(3, 10)):
                    async with NamedTemporaryFile(
                        dir=root_td,
                        mode="wb",
                        prefix="large_file_",
                        suffix=".txt",
                        delete=False,  # Delete handled by the directory being deleted
                    ) as ntf:
                        await ntf.write(os.urandom(randint(MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_BYTES * 2)))
                        large_files.append(ntf.name)

                small_files: List[str] = []
                for _ in range(0, randint(8, 15)):
                    async with NamedTemporaryFile(
                        dir=root_td,
                        mode="wb",
                        prefix="small_file_",
                        suffix=".txt",
                        delete=False,  # Delete handled by the directory being deleted
                    ) as ntf:
                        await ntf.write(os.urandom(randint(10, MAX_FILE_SIZE_BYTES - 1)))
                        small_files.append(ntf.name)

                # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
                mock_run_process.return_value.stdout = "".encode()
                mock_run_process.return_value.returncode = 0

                result = await main_async(["run_scan", "-v", "-x", PERSONAL_DATA_SCAN] + large_files + small_files)

                mock_run_process.assert_called()
                assert result == 1

    async def test_run_scan_with_blocked_files(self):
        async with (
            TemporaryDirectory() as root_td,
        ):
            with patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process:
                blocked_files: List[str] = []
                for file_extension in [".pdf", ".xlsx", ".bak", ".pem"]:
                    async with NamedTemporaryFile(
                        dir=root_td,
                        mode="wb",
                        suffix=file_extension,
                        delete=False,  # Delete handled by the directory being deleted
                    ) as ntf:
                        blocked_files.append(ntf.name)

                mock_run_process.return_value.stdout = "".encode()
                mock_run_process.return_value.returncode = 0

                result = await main_async(["run_scan", "-v"] + blocked_files)

                mock_run_process.assert_called()
                assert result == 1

    async def test_run_scan_with_no_failures(self):
        async with (
            TemporaryDirectory() as root_td,
            TemporaryDirectory(dir=root_td) as sub_td,
            NamedTemporaryFile(dir=root_td, mode="w+", prefix="empty_file_", suffix=".txt") as root_file,
            NamedTemporaryFile(dir=sub_td, mode="w+", prefix="no_personal_data", suffix=".txt") as dir_file2,
        ):
            with patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process:
                await root_file.write("No personal data")
                await root_file.seek(0)

                await dir_file2.write("Nothing to see here")
                await dir_file2.seek(0)

                # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
                mock_run_process.return_value.stdout = "".encode()
                mock_run_process.return_value.returncode = 0

                result = await main_async(["run_scan", "-v", root_file.name, dir_file2.name])

                mock_run_process.assert_called()
                assert result == 0
