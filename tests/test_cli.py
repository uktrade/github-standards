import sys
from unittest import mock

import pytest
from src.cli import get_hook_class, main as main_function, hooks


class TestCLI:
    def test_no_arguments_provided_returns_expected_error(self):
        testargs = []
        with (
            mock.patch.object(sys, "argv", testargs),
        ):
            assert main_function() == 1

    def test_missing_hook_id_argument_returns_expected_error(self):
        testargs = ["hooks-cli"]
        with mock.patch.object(sys, "argv", testargs), pytest.raises(SystemExit):
            main_function()

    def test_unknown_hook_id_argument_returns_expected_error(self):
        testargs = ["hooks-cli", "--hook-id=a"]
        with mock.patch.object(sys, "argv", testargs):
            assert main_function() == 1

    def test_hook_with_failing_validation_returns_expected_error(self):
        testargs = ["hooks-cli", "--hook-id=a", "--verbose"]

        mock_hook = mock.MagicMock()
        mock_hook.validate_args = mock.MagicMock(return_value=False)

        mock_hook_class = mock.MagicMock()
        mock_hook_class.return_value = mock_hook

        with mock.patch.object(sys, "argv", testargs), mock.patch("src.cli.get_hook_class") as mock_get_hook_class:
            mock_get_hook_class.return_value = mock_hook_class
            assert main_function() == 1

    def test_hook_with_an_unsuccessful_run_result_returns_expected_error(self):
        testargs = ["hooks-cli", "--hook-id=a", "--verbose"]

        mock_hook = mock.MagicMock()
        mock_hook.validate_args = mock.MagicMock(return_value=True)
        mock_hook.run = mock.MagicMock(return_value=False)

        mock_hook_class = mock.MagicMock()
        mock_hook_class.return_value = mock_hook

        with mock.patch.object(sys, "argv", testargs), mock.patch("src.cli.get_hook_class") as mock_get_hook_class:
            mock_get_hook_class.return_value = mock_hook_class
            assert main_function() == 1

    def test_hook_with_an_successful_run_result_returns_expected_error(self):
        testargs = ["hooks-cli", "--hook-id=a", "--verbose"]

        mock_hook = mock.MagicMock()
        mock_hook.validate_args = mock.MagicMock(return_value=True)
        mock_hook.run = mock.MagicMock(return_value=True)

        mock_hook_class = mock.MagicMock()
        mock_hook_class.return_value = mock_hook

        with mock.patch.object(sys, "argv", testargs), mock.patch("src.cli.get_hook_class") as mock_get_hook_class:
            mock_get_hook_class.return_value = mock_hook_class
            assert main_function() == 0

    @pytest.mark.parametrize("hook_id", ([hook_id for hook_id in hooks]))
    def test_all_known_hook_ids_return_class(self, hook_id):
        assert get_hook_class(hook_id) is not None
