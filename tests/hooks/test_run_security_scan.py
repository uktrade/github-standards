import tempfile
import requests
import requests_mock

from unittest.mock import patch
from src.hooks.config import RELEASE_CHECK_URL
from src.hooks.run_security_scan import RunSecurityScan


class TestRunSecurityScan:
    def test_validate_args_returns_true(self):
        assert RunSecurityScan().validate_args() is True

    def test_validate_hook_settings_with_dbt_hooks_repo_present_without_rev_element_in_pre_commit_file_returns_false(self):
        yaml = b"""
        repos:
            - repo: https://github.com/uktrade/github-standards
        """

        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(RunSecurityScan, "_skip_check", return_value=False),
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
            patch.object(RunSecurityScan, "_skip_check", return_value=False),
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
            patch.object(RunSecurityScan, "_skip_check", return_value=False),
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
            patch.object(RunSecurityScan, "_skip_check", return_value=False),
            requests_mock.Mocker() as m,
        ):
            m.get(RELEASE_CHECK_URL, json={"tag_name": "v1"})
            tf.write(yaml)
            tf.seek(0)

            assert RunSecurityScan().validate_hook_settings() is True

    def test_run_returns_true(self):
        assert RunSecurityScan().run().success is True
