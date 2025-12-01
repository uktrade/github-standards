import tempfile

from pytest_subprocess import FakeProcess


from src.hooks.cli import main as main_function
from src.hooks.config import TRUFFLEHOG_EXCLUSIONS_FILE_PATH, TRUFFLEHOG_ERROR_CODE, TRUFFLEHOG_VERBOSE_LOG_LEVEL
from src.hooks.trufflehog.vendors import AllowedTrufflehogVendor


class TestCLI:
    def test_run_scan_with_secret_data(self):
        with (
            tempfile.TemporaryDirectory(prefix="root_dir_") as root_td,
            tempfile.TemporaryDirectory(dir=root_td, prefix="sub_dir_1_") as sub_td,
            tempfile.NamedTemporaryFile(dir=root_td, mode="w+", prefix="has_personal_data_", suffix=".txt") as root_file,
            tempfile.NamedTemporaryFile(dir=sub_td, mode="w+", prefix="empty_file_", suffix=".txt"),
            tempfile.NamedTemporaryFile(dir=sub_td, mode="w+", prefix="no_personal_data", suffix=".txt") as dir_file2,
            FakeProcess() as fake_process,
        ):
            root_file.write("My name is John Smith")
            root_file.write("My email is john.smith@test.com")
            root_file.seek(0)

            dir_file2.write("Nothing to see here")
            dir_file2.seek(0)

            # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
            fake_process.register(
                [
                    "trufflehog",
                    "filesystem",
                    "--fail",
                    "--no-update",
                    "--results=verified,unknown",
                    f"--log-level={TRUFFLEHOG_VERBOSE_LOG_LEVEL}",
                    f"--exclude-paths={TRUFFLEHOG_EXCLUSIONS_FILE_PATH}",
                    f"--include-detectors={AllowedTrufflehogVendor.all_vendor_codes_as_str()}",
                    root_td,
                ],
                stdout="Error found in the trufflehog scan",
                returncode=TRUFFLEHOG_ERROR_CODE,
            )

            assert main_function(["run_scan", "-v", root_td]) == 1

    def test_run_scan_with_personal_data(self):
        with (
            tempfile.TemporaryDirectory(prefix="root_dir_") as root_td,
            tempfile.TemporaryDirectory(dir=root_td, prefix="sub_dir_1_") as sub_td,
            tempfile.NamedTemporaryFile(dir=root_td, mode="w+", prefix="has_personal_data_", suffix=".txt") as root_file,
            tempfile.NamedTemporaryFile(dir=sub_td, mode="w+", prefix="empty_file_", suffix=".txt"),
            tempfile.NamedTemporaryFile(dir=sub_td, mode="w+", prefix="no_personal_data", suffix=".txt") as dir_file2,
            FakeProcess() as fake_process,
        ):
            root_file.write("My name is John Smith")
            root_file.write("My email is john.smith@test.com")
            root_file.seek(0)

            dir_file2.write("Nothing to see here")
            dir_file2.seek(0)

            # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
            fake_process.register(
                [
                    "trufflehog",
                    "filesystem",
                    "--fail",
                    "--no-update",
                    "--results=verified,unknown",
                    f"--log-level={TRUFFLEHOG_VERBOSE_LOG_LEVEL}",
                    f"--exclude-paths={TRUFFLEHOG_EXCLUSIONS_FILE_PATH}",
                    f"--include-detectors={AllowedTrufflehogVendor.all_vendor_codes_as_str()}",
                    root_file.name,
                ],
                stdout="Called the trufflehog scanning tool",
                returncode=0,
            )

            assert main_function(["run_scan", "-v", root_file.name]) == 1

    def test_run_scan_with_no_failures(self):
        with (
            tempfile.TemporaryDirectory() as root_td,
            tempfile.TemporaryDirectory(dir=root_td) as sub_td,
            tempfile.NamedTemporaryFile(dir=root_td, mode="w+", prefix="empty_file_", suffix=".txt") as root_file,
            tempfile.NamedTemporaryFile(dir=sub_td, mode="w+", prefix="no_personal_data", suffix=".txt") as dir_file2,
            FakeProcess() as fake_process,
        ):
            root_file.write("No personal data")
            root_file.seek(0)

            dir_file2.write("Nothing to see here")
            dir_file2.seek(0)

            # trufflehog needs to be installed, mock the subprocess.run call to avoid calling directly
            scanner = fake_process.register(
                [
                    "trufflehog",
                    "filesystem",
                    "--fail",
                    "--no-update",
                    "--results=verified,unknown",
                    f"--log-level={TRUFFLEHOG_VERBOSE_LOG_LEVEL}",
                    f"--exclude-paths={TRUFFLEHOG_EXCLUSIONS_FILE_PATH}",
                    f"--include-detectors={AllowedTrufflehogVendor.all_vendor_codes_as_str()}",
                    root_file.name,
                    dir_file2.name,
                ],
                stdout="Called the trufflehog scanning tool",
                returncode=0,
            )

            assert main_function(["run_scan", "-v", root_file.name, dir_file2.name]) == 0
            assert scanner.was_called()
