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
    def test_get_args_with_verbose_true_uses_verbose_trufflehog_log_level(self):
        assert f"--log-level={TRUFFLEHOG_VERBOSE_LOG_LEVEL}" in TrufflehogScanner(verbose=True)._get_args([])

    def test_get_args_with_verbose_false_uses_info_trufflehog_log_level(self):
        assert f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}" in TrufflehogScanner(verbose=False)._get_args([])

    def test_get_args_without_exclusions_file_does_not_have_exclude_arg_for_trufflehog(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            assert f"--exclude-paths={TRUFFLEHOG_EXCLUSIONS_FILE_PATH}" not in TrufflehogScanner()._get_args([])

    def test_get_args_with_exclusions_file_present_includes_exclude_arg_for_trufflehog(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            assert f"--exclude-paths={TRUFFLEHOG_EXCLUSIONS_FILE_PATH}" in TrufflehogScanner()._get_args([])

    def test_get_args_with_github_action_true_uses_git_scanning_mode(self):
        args = TrufflehogScanner()._get_args(paths=["/folder1"], github_action=True)
        assert "file:///folder1" in args
        assert "git" in args

    def test_get_args_with_github_action_false_uses_filesystem_scanning_mode(self):
        paths = ["1.txt", "2.txt", "3.txt"]
        args = TrufflehogScanner()._get_args(paths=paths, github_action=False)
        assert "filesystem" in args
        for file in paths:
            assert file in args

    def test_get_args_expected_vendor_codes_are_added_to_trufflehog_args(self):
        assert "--include-detectors=A,B" in TrufflehogScanner()._get_args([], allowed_vendor_codes=["A", "B"])

    def test_get_args_returns_all_expected_args(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            assert TrufflehogScanner()._get_args(
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

    def test_scan_with_trufflehog_error_code_returns_error_response(self, fp):
        with (
            patch.object(TrufflehogScanner, "_get_args") as mock_args,
            patch("src.hooks.trufflehog.scanner.Proxy"),
            patch.object(TrufflehogScanner, "_get_trufflehog_env_vars") as mock_env,
        ):
            mock_args.return_value = ["arg1", "arg2"]
            mock_env.return_value = {"env_1": "true"}

            scanner = fp.register(
                ["arg1", "arg2"],
                stdout="Called the scanning tool",
                returncode=TRUFFLEHOG_ERROR_CODE,
            )

            result = TrufflehogScanner().scan()

            assert result is not None
            assert scanner.was_called()
            assert scanner.calls[0].kwargs == {
                "text": True,
                "env": {"env_1": "true"},
                "shell": False,
                "stderr": -1,
                "stdout": -1,
            }

    def test_scan_with_trufflehog_success_returns_no_error_response(self, fp):
        with (
            patch.object(TrufflehogScanner, "_get_args") as mock_args,
            patch("src.hooks.trufflehog.scanner.Proxy"),
            patch.object(TrufflehogScanner, "_get_trufflehog_env_vars") as mock_env,
        ):
            mock_args.return_value = ["arg1", "arg2"]
            mock_env.return_value = {"env_1": "true"}

            scanner = fp.register(
                ["arg1", "arg2"],
                stdout="Called the scanning tool",
                returncode=0,
            )

            result = TrufflehogScanner().scan()

            assert result is None
            assert scanner.was_called()
            assert scanner.calls[0].kwargs == {
                "text": True,
                "env": {"env_1": "true"},
                "shell": False,
                "stderr": -1,
                "stdout": -1,
            }
