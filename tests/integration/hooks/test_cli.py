from anyio import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import patch


from src.hooks.cli import main_async
from src.hooks.config import TRUFFLEHOG_ERROR_CODE


class TestCLI:
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
                assert mock_run_process.was_called()
                assert result == 1

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
                assert mock_run_process.was_called()
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
                assert result == 0
                assert mock_run_process.was_called()
