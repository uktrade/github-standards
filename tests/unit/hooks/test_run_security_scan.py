from pathlib import Path
import requests
import requests_mock
import tempfile

from unittest.mock import patch
from src.hooks.config import (
    RELEASE_CHECK_URL,
)
from src.hooks.run_security_scan import RunSecurityScan


class TestRunSecurityScan:
    def test_validate_args_without_path_list_returns_false(self):
        assert RunSecurityScan(paths=None).validate_args() is False

    def test_validate_args_with_empty_path_list_returns_false(self):
        assert RunSecurityScan(paths=[]).validate_args() is False

    def test_validate_args_single_path_list_returns_true(self):
        assert RunSecurityScan(paths=["a.txt"]).validate_args() is True

    def test_validate_args_multiple_path_list_returns_true(self):
        assert RunSecurityScan(paths=["a.txt", "b.txt", "c.txt"]).validate_args() is True

    def test_validate_args_without_path_list_with_github_actions_mode_true_returns_false(self):
        assert RunSecurityScan(paths=None, github_action=True).validate_args() is False

    def test_validate_args_with_multiple_path_list_with_github_actions_mode_true_returns_false(self):
        assert RunSecurityScan(paths=["a.txt", "b.txt", "c.txt"], github_action=True).validate_args() is False

    def test_validate_args_with_single_file_in_path_list_with_github_actions_mode_true_returns_false(self):
        assert RunSecurityScan(paths=["a.txt"], github_action=True).validate_args() is False

    def test_validate_args_with_single_directory_in_path_list_with_github_actions_mode_true_returns_true(self):
        with patch.object(Path, "is_dir") as mock_is_dir:
            mock_is_dir.return_value = True
            assert RunSecurityScan(paths=["/a/b/c"], github_action=True).validate_args() is True

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

    def test_run_with_error_returns_false(
        self,
    ):
        with (
            patch("src.hooks.run_security_scan.TrufflehogScanner.scan") as mock_scanner,
            patch("src.hooks.run_security_scan.Proxy"),
        ):
            mock_scanner.return_value = "Error Occured"
            assert RunSecurityScan().run().success is False

    def test_run_without_error_returns_true(
        self,
    ):
        with (
            patch("src.hooks.run_security_scan.TrufflehogScanner.scan") as mock_scanner,
            patch("src.hooks.run_security_scan.Proxy"),
        ):
            mock_scanner.return_value = None
            assert RunSecurityScan().run().success is True
