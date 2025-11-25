import tempfile

from pytest_subprocess import FakeProcess


from src.hooks.cli import main as main_function
from src.hooks.config import TRUFFLEHOG_EXCLUSIONS_FILE_PATH, TRUFFLEHOG_VERBOSE_LOG_LEVEL
from src.hooks.trufflehog.vendors import AllowedTrufflehogVendor


class TestCLI:
    def test_run_scan(self):
        with (
            tempfile.NamedTemporaryFile(mode="r+", suffix=".txt") as file,
            FakeProcess() as fake_process,
        ):
            file.write('aws_access_key_id = "AKIAQYLPMN5HHHFPZAM1"')
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
                    file.name,
                ],
                stdout="Called the trufflehog scanning tool",
                returncode=0,
            )

            main_function(["run_scan", "-v", file.name])
            assert scanner.was_called()
