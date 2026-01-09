from pathlib import Path
from unittest.mock import patch

from anyio import NamedTemporaryFile
from src.hooks.hooks_base import Hook, HookRunResult


class HooksBaseTestImplementation(Hook):
    def validate_args(self) -> bool:
        return True

    async def _validate_hook_settings(self, dbt_repo_config) -> bool:
        return False

    async def run(self) -> HookRunResult:
        return HookRunResult()


class TestHooksBase:
    def test_init_assigns_paths_as_empty_list_when_paths_is_none(self):
        assert HooksBaseTestImplementation().paths == []

    def test_init_assigns_paths_as_same_list_when_paths_is_list_of_strings(self):
        assert HooksBaseTestImplementation(paths=["a", "b"]).paths == ["a", "b"]

    @patch("src.hooks.hooks_base.FORCE_HOOK_CHECKS", "0")
    async def test_validate_hook_settings_when_force_hook_checks_false_returns_true(self):
        assert await HooksBaseTestImplementation().validate_hook_settings() is True

    @patch("src.hooks.hooks_base.FORCE_HOOK_CHECKS", "1")
    async def test_validate_hook_settings_when_force_hook_checks_true_returns_true(self):
        assert await HooksBaseTestImplementation().validate_hook_settings() is False

    async def test_validate_hook_settings_with_missing_pre_commit_file_returns_false(self):
        with (
            patch.object(Path, "exists") as mock_exists,
            patch.object(HooksBaseTestImplementation, "_enforce_settings_checks", return_value=True),
        ):
            mock_exists.return_value = False
            assert await HooksBaseTestImplementation().validate_hook_settings() is False

    async def test_validate_hook_settings_with_invalid_content_in_pre_commit_file_returns_false(self):
        async with NamedTemporaryFile() as tf:
            with (
                patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
                patch.object(HooksBaseTestImplementation, "_enforce_settings_checks", return_value=True),
            ):
                await tf.write(b"Not valid yaml")
                await tf.seek(0)

                assert await HooksBaseTestImplementation().validate_hook_settings() is False

    async def test_validate_hook_settings_with_dbt_hooks_repo_missing_in_pre_commit_file_returns_false(self):
        valid_yaml = b"""
        repos:
            - repo: https://github.com/pre-commit/pre-commit-hooks
              rev: v6.0.0
              hooks:
              - id: no-commit-to-branch
        """
        async with NamedTemporaryFile() as tf:
            with (
                patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
                patch.object(HooksBaseTestImplementation, "_enforce_settings_checks", return_value=True),
            ):
                await tf.write(valid_yaml)
                await tf.seek(0)

                assert await HooksBaseTestImplementation().validate_hook_settings() is False

    async def test_validate_hook_settings_with_dbt_hooks_repo_present_multiple_times_in_pre_commit_file_returns_false(self):
        valid_yaml = b"""
        repos:
            - repo: https://github.com/uktrade/github-standards
              rev: v111
              hooks:
                - id: validate-security-scan
                - id: run-security-scan
            - repo: https://github.com/uktrade/github-standards
              rev: v111
              hooks:
                - id: validate-security-scan
                - id: run-security-scan
            - repo: https://github.com/uktrade/github-standards
              rev: v111
              hooks:
                - id: validate-security-scan
                - id: run-security-scan
        """
        async with NamedTemporaryFile() as tf:
            with (
                patch("src.hooks.hooks_base.PRE_COMMIT_FILE", tf.name),
                patch.object(HooksBaseTestImplementation, "_enforce_settings_checks", return_value=True),
            ):
                await tf.write(valid_yaml)
                await tf.seek(0)

                assert await HooksBaseTestImplementation().validate_hook_settings() is False
