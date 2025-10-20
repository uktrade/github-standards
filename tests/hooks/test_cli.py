import sys
import pytest

from unittest import mock

from src.hooks.cli import main as main_function, parse_args
from src.hooks.config import GITHUB_ACTION_PR, GITHUB_ACTION_REPO
from src.hooks.hooks_base import HookRunResult


class TestCLI:
    class TestParseArgs:
        def test_parse_args_without_subcommand_returns_error(self):
            testargs = [""]
            with mock.patch.object(sys, "argv", testargs), pytest.raises(SystemExit):
                parse_args(testargs)

        def test_parse_args_with_unknown_subcommand_returns_error(self):
            testargs = ["invalid"]
            with mock.patch.object(sys, "argv", testargs), pytest.raises(SystemExit):
                parse_args(testargs)

        def test_parse_args_for_run_without_files_returns_expected_args(self):
            testargs = ["run_scan"]
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == []
                assert result.verbose is False

        @pytest.mark.parametrize("verbose", (["-v", "--verbose"]))
        def test_parse_args_for_run_with_verbose_returns_expected_args(self, verbose):
            files = ["a.txt", "b.txt"]
            testargs = ["run_scan", verbose] + files
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == files
                assert result.verbose is True

        def test_parse_args_for_run_without_verbose_returns_expected_args(self):
            files = ["a.txt", "b.txt"]
            testargs = ["run_scan"] + files
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == files
                assert result.verbose is False

        @pytest.mark.parametrize(
            "github_actions_arg_name",
            ["-g", "--github-action"],
        )
        @pytest.mark.parametrize(
            "github_actions_value",
            [GITHUB_ACTION_PR, GITHUB_ACTION_REPO],
        )
        def test_parse_args_for_run_with_github_actions_returns_expected_args(
            self, github_actions_arg_name, github_actions_value
        ):
            files = ["a.txt", "b.txt"]
            testargs = ["run_scan", github_actions_arg_name, github_actions_value] + files
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == files
                assert result.verbose is False
                assert result.github_action == github_actions_value

        def test_parse_args_for_run_without_github_actions_returns_expected_args(self):
            files = ["a.txt", "b.txt"]
            testargs = ["run_scan"] + files
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == files
                assert result.verbose is False
                assert result.github_action is None

        def test_parse_args_for_validate_without_files_returns_expected_args(self):
            testargs = ["validate_scan"]
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == []
                assert result.verbose is False

        @pytest.mark.parametrize("verbose", (["-v", "--verbose"]))
        def test_parse_args_for_validate_with_verbose_returns_expected_args(self, verbose):
            files = ["a.txt", "b.txt"]
            testargs = ["validate_scan", verbose] + files
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == files
                assert result.verbose is True

        def test_parse_args_for_validate_without_verbose_returns_expected_args(self):
            files = ["a.txt", "b.txt"]
            testargs = ["validate_scan"] + files
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.files == files
                assert result.verbose is False

    class TestMain:
        def test_no_arguments_provided_returns_expected_error(self):
            testargs = []
            with mock.patch.object(sys, "argv", testargs):
                assert main_function() == 1

        def test_hook_with_failing_validate_args_returns_expected_error(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=False)

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert main_function() == 1

        def test_hook_with_failing_validate_hook_settings_returns_expected_error(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=True)
            mock_hook.validate_hook_settings = mock.MagicMock(return_value=False)

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert main_function() == 1

        def test_hook_with_an_unsuccessful_run_result_returns_expected_error(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=True)
            mock_hook.validate_hook_settings = mock.MagicMock(return_value=True)
            mock_hook.run = mock.MagicMock(return_value=HookRunResult(success=False))

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert main_function() == 1

        def test_hook_with_a_successful_run_result_returns_expected_error(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=True)
            mock_hook.validate_hook_settings = mock.MagicMock(return_value=True)
            mock_hook.run = mock.MagicMock(return_value=HookRunResult(success=True))

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert main_function() == 0
