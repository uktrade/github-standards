from pathlib import Path
from unittest.mock import patch
from src.hooks.config import (
    TRUFFLEHOG_ERROR_CODE,
    TRUFFLEHOG_EXCLUSIONS_FILE_PATH,
    TRUFFLEHOG_INFO_LOG_LEVEL,
    TRUFFLEHOG_VERBOSE_LOG_LEVEL,
)
from src.hooks.trufflehog.scanner import TrufflehogScanner


class TestTrufflehogScanner:
    async def test_get_args_with_verbose_true_uses_verbose_trufflehog_log_level(self):
        assert f"--log-level={TRUFFLEHOG_VERBOSE_LOG_LEVEL}" in await TrufflehogScanner(verbose=True)._get_args([])

    async def test_get_args_with_verbose_false_uses_info_trufflehog_log_level(self):
        assert f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}" in await TrufflehogScanner(verbose=False)._get_args([])

    async def test_get_args_without_exclusions_file_does_not_have_exclude_arg_for_trufflehog(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            assert f"--exclude-paths={TRUFFLEHOG_EXCLUSIONS_FILE_PATH}" not in await TrufflehogScanner()._get_args([])

    async def test_get_args_with_exclusions_file_present_includes_exclude_arg_for_trufflehog(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            assert f"--exclude-paths={TRUFFLEHOG_EXCLUSIONS_FILE_PATH}" in await TrufflehogScanner()._get_args([])

    async def test_get_args_with_github_action_true_uses_git_scanning_mode(self):
        args = await TrufflehogScanner()._get_args(paths=["/folder1"], github_action=True)
        assert "file:///folder1" in args
        assert "git" in args

    async def test_get_args_with_github_action_false_uses_filesystem_scanning_mode(self):
        paths = ["1.txt", "2.txt", "3.txt"]
        args = await TrufflehogScanner()._get_args(paths=paths, github_action=False)
        assert "filesystem" in args
        for file in paths:
            assert file in args

    async def test_get_args_expected_vendor_codes_are_added_to_trufflehog_args(self):
        assert "--include-detectors=A,B" in await TrufflehogScanner()._get_args([], allowed_vendor_codes=["A", "B"])

    async def test_get_args_returns_all_expected_args(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            assert await TrufflehogScanner()._get_args(
                ["1.txt"],
                allowed_vendor_codes=[
                    "a",
                    "b",
                    "c",
                ],
            ) == [
                "trufflehog",
                "filesystem",
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}",
                "--include-detectors=a,b,c",
                "1.txt",
            ]

    async def test_scan_with_trufflehog_error_code_returns_error_response(self):
        with (
            patch.object(TrufflehogScanner, "_get_args") as mock_args,
            patch("src.hooks.trufflehog.scanner.Proxy"),
            patch.object(TrufflehogScanner, "_get_trufflehog_env_vars") as mock_env,
            patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process,
        ):
            mock_args.return_value = ["arg1", "arg2"]
            mock_env.return_value = {"env_1": "true"}

            mock_run_process.return_value.stdout = "Found keys".encode()
            mock_run_process.return_value.stderr = "Called the scanning tool and keys were found".encode()
            mock_run_process.return_value.returncode = TRUFFLEHOG_ERROR_CODE

            result = await TrufflehogScanner().scan()
            mock_run_process.assert_awaited_once_with(
                mock_args.return_value,
                check=False,
                env=mock_env.return_value,
            )

            assert result.detected_keys == "Found keys"

    async def test_scan_with_trufflehog_success_returns_no_error_response(self):
        with (
            patch.object(TrufflehogScanner, "_get_args") as mock_args,
            patch("src.hooks.trufflehog.scanner.Proxy"),
            patch.object(TrufflehogScanner, "_get_trufflehog_env_vars") as mock_env,
            patch("src.hooks.trufflehog.scanner.run_process") as mock_run_process,
        ):
            mock_args.return_value = ["arg1", "arg2"]
            mock_env.return_value = {"env_1": "true"}

            mock_run_process.return_value.stdout = "".encode()
            mock_run_process.return_value.returncode = 0

            result = await TrufflehogScanner().scan()
            mock_run_process.assert_awaited_once_with(
                mock_args.return_value,
                check=False,
                env=mock_env.return_value,
            )
            assert result.detected_keys is None
