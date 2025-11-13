from unittest.mock import patch
from src.hooks.config import (
    TRUFFLEHOG_ERROR_CODE,
    TRUFFLEHOG_INFO_LOG_LEVEL,
    TRUFFLEHOG_VERBOSE_LOG_LEVEL,
)
from src.hooks.trufflehog.scanner import TrufflehogScanner


class TestTrufflehogScanner:
    def test_with_verbose_true_uses_verbose_trufflehog_log_level(self):
        assert f"--log-level={TRUFFLEHOG_VERBOSE_LOG_LEVEL}" in TrufflehogScanner(verbose=True)._get_args()

    def test_with_verbose_false_uses_info_trufflehog_log_level(self):
        assert f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}" in TrufflehogScanner(verbose=False)._get_args()

    def test_without_exclusions_file_does_not_have_exclude_arg_for_trufflehog(self):
        with patch("src.hooks.trufflehog.scanner.os.path.exists") as mock_isfile:
            mock_isfile.return_value = False
            assert "--exclude-paths=trufflehog-excludes.txt" not in TrufflehogScanner()._get_args()

    def test_with_exclusions_file_present_includes_exclude_arg_for_trufflehog(self):
        with patch("src.hooks.trufflehog.scanner.os.path.exists") as mock_isfile:
            mock_isfile.return_value = True
            assert "--exclude-paths=trufflehog-excludes.txt" in TrufflehogScanner()._get_args()

    def test_with_github_action_true_uses_git_scanning_mode(self):
        args = TrufflehogScanner(paths=["/folder1"], github_action=True)._get_args()
        assert "file:///folder1" in args
        assert "git" in args

    def test_with_github_action_false_uses_filesystem_scanning_mode(self):
        paths = ["1.txt", "2.txt", "3.txt"]
        args = TrufflehogScanner(github_action=False, paths=paths)._get_args()
        assert "filesystem" in args
        for file in paths:
            assert file in args

    def test_expected_vendor_codes_are_added_to_trufflehog_args(self):
        assert "--include-detectors=A,B" in TrufflehogScanner(allowed_vendor_codes=["A", "B"])._get_args()

    def test_all_args(self):
        assert TrufflehogScanner()._get_args() == [
            "trufflehog",
            "filesystem",
            "--fail",
            "--no-update",
            "--results=verified,unknown",
            f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}",
            "--include-detectors=",
        ]

    def test_scan_with_trufflehog_error_code_returns_error_response(self, fp):
        with patch.object(TrufflehogScanner, "_get_args") as mock_args:
            mock_args.return_value = ["arg1", "arg2"]
            scanner = fp.register(
                ["arg1", "arg2"],
                stdout="Called the scanning tool",
                returncode=TRUFFLEHOG_ERROR_CODE,
            )
            result = TrufflehogScanner().scan({"env_1": "true"})
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
        with patch.object(TrufflehogScanner, "_get_args") as mock_args:
            mock_args.return_value = ["arg1", "arg2"]
            scanner = fp.register(
                ["arg1", "arg2"],
                stdout="Called the scanning tool",
                returncode=0,
            )
            result = TrufflehogScanner().scan({})
            assert result is None
            assert scanner.was_called()
