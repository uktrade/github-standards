import tempfile
import src.config

from unittest.mock import patch

from src.hooks.validate_security_scan import ValidateSecurityScan


class TestValidateSecurityScan:
    def test_validate_args_none_file_list_returns_false(self):
        assert ValidateSecurityScan(files=None).validate_args() is False

    def test_validate_args_empty_file_list_returns_false(self):
        assert ValidateSecurityScan(files=[]).validate_args() is False

    def test_validate_args_file_list_with_more_than_one_item_returns_false(self):
        assert ValidateSecurityScan(files=["a.txt", "b.txt"]).validate_args() is False

    def test_validate_args_file_list_with_one_item_returns_true(self):
        assert ValidateSecurityScan(files=["a.txt"]).validate_args() is True

    def test_validate_hook_settings_with_dbt_hooks_repo_present_without_hooks_element_in_pre_commit_file_returns_false(self):
        valid_yaml = b"""
        repos:
            - repo: https://github.com/uktrade/dbt-hooks
              rev: v111
        """
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(ValidateSecurityScan, "_skip_check", return_value=False),
        ):
            tf.write(valid_yaml)
            tf.seek(0)

            assert ValidateSecurityScan().validate_hook_settings() is False

    def test_validate_hook_settings_with_dbt_hooks_repo_present_without_ids_element_in_pre_commit_file_returns_false(self):
        valid_yaml = b"""
        repos:
            - repo: https://github.com/uktrade/dbt-hooks
              rev: v111
              hooks:
                - version
        """
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(ValidateSecurityScan, "_skip_check", return_value=False),
        ):
            tf.write(valid_yaml)
            tf.seek(0)

            assert ValidateSecurityScan().validate_hook_settings() is False

    def test_validate_hook_settings_with_dbt_hooks_repo_present_without_mandatory_is_in_pre_commit_file_returns_false(self):
        valid_yaml = b"""
        repos:
            - repo: https://github.com/uktrade/dbt-hooks
              rev: v111
              hooks:
                - id: something
        """
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(ValidateSecurityScan, "_skip_check", return_value=False),
        ):
            tf.write(valid_yaml)
            tf.seek(0)

            assert ValidateSecurityScan().validate_hook_settings() is False

    def test_validate_hook_settings_with_repo_and_hooks_present_in_pre_commit_file_returns_true(self):
        valid_yaml = b"""
        repos:
            - repo: https://github.com/pre-commit/pre-commit-hooks
              rev: v6.0.0  
              hooks:
              - id: no-commit-to-branch
            - repo: https://github.com/uktrade/dbt-hooks
              rev: v111
              hooks:
                - id: validate-security-scan
                - id: run-security-scan
        """
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch("src.hooks_base.PRE_COMMIT_FILE", tf.name),
            patch.object(ValidateSecurityScan, "_skip_check", return_value=False),
        ):
            tf.write(valid_yaml)
            tf.seek(0)

            assert ValidateSecurityScan().validate_hook_settings() is True

    def test_run_when_validate_hook_settings_failes_returns_error_code(self):
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch.object(ValidateSecurityScan, "validate_hook_settings", return_value=False),
        ):
            assert ValidateSecurityScan(files=[tf.name]).run() is False

    def test_run_with_file_with_no_contents_returns_error_code(self):
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch.object(ValidateSecurityScan, "validate_hook_settings", return_value=True),
        ):
            assert ValidateSecurityScan(files=[tf.name]).run() is False

    def test_run_with_file_with_message_has_signed_off_by_trailer_added(self):
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch.object(ValidateSecurityScan, "validate_hook_settings", return_value=True),
        ):
            tf.write(b"A helpful commit message")
            tf.seek(0)
            assert ValidateSecurityScan(files=[tf.name]).run() is True

            assert tf.read().decode("UTF-8") == f"A helpful commit message\n{src.config.SIGNED_OFF_BY_TRAILER}"

    def test_run_with_file_with_multiline_message_has_signed_off_by_trailer_added(self):
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch.object(ValidateSecurityScan, "validate_hook_settings", return_value=True),
        ):
            tf.writelines(line + b"\n" for line in [b"A", b"helpful", b"commit", b" message"])
            tf.seek(0)

            assert ValidateSecurityScan(files=[tf.name]).run() is True

            assert tf.read().decode("UTF-8") == f"A\nhelpful\ncommit\n message\n\n{src.config.SIGNED_OFF_BY_TRAILER}"

    def test_run_with_file_with_existing_signed_off_header_is_replaced(self):
        with (
            tempfile.NamedTemporaryFile() as tf,
            patch.object(ValidateSecurityScan, "validate_hook_settings", return_value=True),
        ):
            tf.write(b"A helpful commit message\nSigned-off-by: SOMETHING ELSE")
            tf.seek(0)

            assert ValidateSecurityScan(files=[tf.name]).run() is True

            assert tf.read().decode("UTF-8") == f"A helpful commit message\n\n{src.config.SIGNED_OFF_BY_TRAILER}"
