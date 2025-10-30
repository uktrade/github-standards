import pytest
import requests
import requests_mock
import tempfile

from unittest.mock import MagicMock, patch
from src.hooks.config import GITHUB_ACTION_PR, GITHUB_ACTION_REPO
from src.hooks.config import (
    RELEASE_CHECK_URL,
    TRUFFLEHOG_ERROR_CODE,
    TRUFFLEHOG_INFO_LOG_LEVEL,
    TRUFFLEHOG_VERBOSE_LOG_LEVEL,
)
from src.hooks.run_security_scan import RunSecurityScan


class TestRunSecurityScan:
    @pytest.fixture(autouse=True)
    def hide_config_fixture(self, request):
        if "noautofixt" in request.keywords:
            yield
        else:
            mock_config_parser = MagicMock(return_value=None)
            with patch("src.hooks.run_security_scan.RunSecurityScan._get_trufflehog_detectors", mock_config_parser):
                yield mock_config_parser

    def test_validate_args_without_file_list_returns_false(self):
        assert RunSecurityScan(files=None).validate_args() is False

    def test_validate_args_without_file_list_with_github_actions_mode_true_returns_true(self):
        assert RunSecurityScan(files=None, github_action=GITHUB_ACTION_PR).validate_args() is True

    def test_validate_args_with_empty_file_list_returns_false(self):
        assert RunSecurityScan(files=[]).validate_args() is False

    def test_validate_args_single_file_list_returns_true(self):
        assert RunSecurityScan(files=["a.txt"]).validate_args() is True

    def test_validate_args_multiple_file_list_returns_true(self):
        assert RunSecurityScan(files=["a.txt", "b.txt", "c.txt"]).validate_args() is True

    def test_validate_hook_settings_with_dbt_hooks_repo_present_without_rev_element_in_pre_commit_file_returns_false(self):
        yaml = b"""
        repos:
            - repo: https://github.com/uktrade/github-standards
        """

        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(RunSecurityScan, "_enforce_settings_checks", return_value=True),
        ):
            tf.write(yaml)
            tf.seek(0)

            assert RunSecurityScan().validate_hook_settings() is False

    def test_validate_hook_settings_with_dbt_hooks_repo_present_with_rev_element_in_pre_commit_file_differs_remote_version_returns_false(
        self,
    ):
        yaml = b"""
        repos:
            - repo: https://github.com/uktrade/github-standards
              rev: v1
        """

        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(RunSecurityScan, "_enforce_settings_checks", return_value=True),
            patch.object(RunSecurityScan, "_get_version_from_remote", return_value="v2"),
        ):
            tf.write(yaml)
            tf.seek(0)

            assert RunSecurityScan().validate_hook_settings() is False

    def test_validate_hook_settings_with_dbt_hooks_repo_present_when_remote_version_http_error_returns_true(
        self,
    ):
        yaml = b"""
        repos:
            - repo: https://github.com/uktrade/github-standards
              rev: v1
        """

        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(RunSecurityScan, "_enforce_settings_checks", return_value=True),
            requests_mock.Mocker() as m,
        ):
            m.get(RELEASE_CHECK_URL, exc=requests.exceptions.HTTPError)
            tf.write(yaml)
            tf.seek(0)

            assert RunSecurityScan().validate_hook_settings() is True

    def test_validate_hook_settings_with_dbt_hooks_repo_present_with_rev_element_in_pre_commit_file_matching_remote_version_returns_true(
        self,
    ):
        yaml = b"""
        repos:
            - repo: https://github.com/uktrade/github-standards
              rev: v1
        """

        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(RunSecurityScan, "_enforce_settings_checks", return_value=True),
            requests_mock.Mocker() as m,
        ):
            m.get(RELEASE_CHECK_URL, json={"tag_name": "v1"})
            tf.write(yaml)
            tf.seek(0)

            assert RunSecurityScan().validate_hook_settings() is True

    @pytest.mark.noautofixt
    def test_get_trufflehog_detectors_returns_expected_detectors(self):
        with patch("src.hooks.run_security_scan.ConfigParser.get") as mock_config_parser:
            mock_config_parser.return_value = "vendor1,vendor2"
            assert RunSecurityScan(files=["a.txt"], verbose=True)._get_trufflehog_detectors() == "vendor1,vendor2"

    @pytest.mark.noautofixt
    def test_get_trufflehog_detectors_returns_none_when_parser_exception_occurs(self):
        with patch("src.hooks.run_security_scan.ConfigParser.get") as mock_config_parser:
            mock_config_parser.side_effect = KeyError()
            assert RunSecurityScan(files=["a.txt"], verbose=True)._get_trufflehog_detectors() is None

    def test_run_with_verbose_true_uses_verbose_trufflehog_log_level(self, fp):
        scanner = fp.register(
            [
                "trufflehog",
                "filesystem",
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                f"--log-level={TRUFFLEHOG_VERBOSE_LOG_LEVEL}",
                fp.any(),
            ],
            stdout="Called the scanning tool",
        )

        assert RunSecurityScan(files=["a.txt"], verbose=True).run().success is True
        assert scanner.was_called()

    def test_run_with_verbose_false_uses_info_trufflehog_log_level(self, fp):
        scanner = fp.register(
            [
                "trufflehog",
                "filesystem",
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}",
                fp.any(),
            ],
            stdout="Called the scanning tool",
        )

        assert RunSecurityScan(files=["a.txt"], verbose=False).run().success is True
        assert scanner.was_called()

    def test_run_with_exclusions_file_present_includes_exclude_arg_for_trufflehog(self, fp):
        scanner = fp.register(
            [
                "trufflehog",
                "filesystem",
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}",
                "--exclude-paths=trufflehog-excludes.txt",
                fp.any(),
            ],
            stdout="Called the scanning tool",
        )

        with patch("src.hooks.run_security_scan.os.path.exists") as mock_isfile:
            mock_isfile.return_value = True

            assert RunSecurityScan(files=["a.txt"], verbose=False).run().success is True
            assert scanner.was_called()

    def test_run_with_config_file_with_detectors_list_includes_detectors_arg_for_trufflehog(self, fp, hide_config_fixture):
        hide_config_fixture.return_value = "vendor1,vendor2"
        scanner = fp.register(
            [
                "trufflehog",
                "filesystem",
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}",
                "--include-detectors=vendor1,vendor2",
                fp.any(),
            ],
            stdout="Called the scanning tool",
        )

        assert RunSecurityScan(files=["a.txt"], verbose=False).run().success is True
        assert scanner.was_called()

    def test_run_with_secrets_found_in_file_list_returns_false(self, fp):
        scanner = fp.register(
            [
                "trufflehog",
                fp.any(),
            ],
            stdout="Error: secrets found",
            returncode=TRUFFLEHOG_ERROR_CODE,
        )
        result = RunSecurityScan(files=["a.txt"]).run()
        assert result.success is False
        assert result.message is not None
        assert scanner.was_called()

    def test_run_with_no_secrets_found_in_file_list_returns_true(self, fp):
        scanner = fp.register(
            [
                "trufflehog",
                fp.any(),
            ],
            stdout="No secrets found",
            returncode=0,
        )

        assert RunSecurityScan(files=["a.txt"]).run().success is True
        assert scanner.was_called()

    def test_run_with_no_secrets_found_in_github_actions_pr_mode_returns_true(self, fp):
        scanner = fp.register(
            [
                "trufflehog",
                "filesystem",
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}",
                ".",
            ],
            stdout="No secrets found",
            returncode=0,
        )

        assert RunSecurityScan(github_action=GITHUB_ACTION_PR).run().success is True
        assert scanner.was_called()

    def test_run_with_no_secrets_found_in_github_actions_repo_mode_returns_true(self, fp):
        scanner = fp.register(
            [
                "trufflehog",
                "git",
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                f"--log-level={TRUFFLEHOG_INFO_LOG_LEVEL}",
                "file://./",
            ],
            stdout="No secrets found",
            returncode=0,
        )

        assert RunSecurityScan(github_action=GITHUB_ACTION_REPO).run().success is True
        assert scanner.was_called()
