import sys
import pytest

from unittest import mock

from src.hooks.cli import main as main_function, main_async, parse_args
from src.hooks.config import PERSONAL_DATA_SCAN, SECURITY_SCAN


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

        def test_parse_args_for_run_without_paths_returns_expected_args(self):
            testargs = ["run_scan"]
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == []
                assert result.verbose is False

        @pytest.mark.parametrize("verbose", (["-v", "--verbose"]))
        def test_parse_args_for_run_with_verbose_returns_expected_args(self, verbose):
            paths = ["a.txt", "b.txt"]
            testargs = ["run_scan", verbose] + paths
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == paths
                assert result.verbose is True

        def test_parse_args_for_run_without_verbose_returns_expected_args(self):
            paths = ["a.txt", "b.txt"]
            testargs = ["run_scan"] + paths
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == paths
                assert result.verbose is False

        def test_parse_args_for_run_with_github_actions_returns_expected_args(
            self,
        ):
            paths = ["a.txt", "b.txt"]
            testargs = ["run_scan", "--github-action"] + paths
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == paths
                assert result.verbose is False
                assert result.github_action is True

        def test_parse_args_for_run_without_github_actions_returns_expected_args(self):
            paths = ["a.txt", "b.txt"]
            testargs = ["run_scan"] + paths
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == paths
                assert result.verbose is False
                assert result.github_action is False

        def test_parse_args_for_run_with_unknown_excluded_scans_throws_error(self):
            paths = ["a.txt", "b.txt"]
            with pytest.raises(SystemExit):
                testargs = ["run_scan", "--excluded-scans", "not_real"] + paths
                with mock.patch.object(sys, "argv", testargs):
                    parse_args(testargs)

        def test_parse_args_for_run_with_all_excluded_scans_returns_expected_args(self):
            paths = ["a.txt", "b.txt"]
            testargs = ["run_scan", "--excluded-scans", SECURITY_SCAN, "--excluded-scans", PERSONAL_DATA_SCAN] + paths
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == paths
                assert result.verbose is False
                assert result.github_action is False
                assert result.excluded_scans == [SECURITY_SCAN, PERSONAL_DATA_SCAN]

        def test_parse_args_for_validate_without_paths_returns_expected_args(self):
            testargs = ["validate_scan"]
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == []
                assert result.verbose is False

        @pytest.mark.parametrize("verbose", (["-v", "--verbose"]))
        def test_parse_args_for_validate_with_verbose_returns_expected_args(self, verbose):
            paths = ["a.txt", "b.txt"]
            testargs = ["validate_scan", verbose] + paths
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == paths
                assert result.verbose is True

        def test_parse_args_for_validate_without_verbose_returns_expected_args(self):
            paths = ["a.txt", "b.txt"]
            testargs = ["validate_scan"] + paths
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.paths == paths
                assert result.verbose is False

    class TestMain:
        def test_no_arguments_provided_returns_expected_error(self):
            testargs = []
            with mock.patch.object(sys, "argv", testargs):
                assert main_function(testargs) == 1

    class TestMainAsync:
        async def test_hook_with_failing_validate_args_returns_expected_error(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=False)

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert await main_async() == 1

        async def test_hook_with_failing_validate_hook_settings_returns_expected_error(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=True)
            mock_hook.validate_hook_settings = mock.AsyncMock(return_value=False)

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert await main_async() == 1

        async def test_hook_with_an_unsuccessful_run_result_returns_expected_exit_code(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=True)
            mock_hook.validate_hook_settings = mock.AsyncMock(return_value=True)

            mock_run_result = mock.MagicMock()
            mock_run_result.run_summary.return_value = "Hook ran with an error"
            mock_run_result.run_success.return_value = False

            mock_run = mock.AsyncMock(return_value=mock_run_result)

            mock_hook.run = mock_run

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert await main_async() == 1

        async def test_hook_with_a_successful_run_result_returns_expected_exit_code(self):
            mock_hook = mock.MagicMock()
            mock_hook.validate_args = mock.MagicMock(return_value=True)
            mock_hook.validate_hook_settings = mock.AsyncMock(return_value=True)

            mock_run_result = mock.MagicMock()
            mock_run_result.run_summary.return_value = "Hook ran successfully"
            mock_run_result.run_success.return_value = True

            mock_run = mock.AsyncMock(return_value=mock_run_result)

            mock_hook.run = mock_run

            mock_args = mock.MagicMock()
            mock_args.hook.return_value = mock_hook

            with mock.patch.object(sys, "argv", [""]), mock.patch("src.hooks.cli.parse_args") as mock_parse_args:
                mock_parse_args.return_value = mock_args
                assert await main_async() == 0
