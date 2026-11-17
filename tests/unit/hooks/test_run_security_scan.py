import asyncio
import json
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.test_utils import TestClient
import pytest
import requests

import pytest_asyncio

from aiohttp import ClientResponseError, ClientSession, web

from pathlib import Path
from presidio_analyzer import RecognizerResult

from unittest.mock import AsyncMock, MagicMock, call, patch

from yarl import URL
from src.hooks.config import (
    LOGGER,
    PERSONAL_DATA_SCAN,
    RELEASE_CHECK_URL,
    SECURITY_SCAN,
)
from src.hooks.presidio.path_filter import PathScanStatus
from src.hooks.presidio.scanner import PersonalDataDetection, PresidioScanResult, PathScanResult
from src.hooks.run_security_scan import RunSecurityScan
from src.hooks.trufflehog.scanner import TrufflehogScanResult


@pytest_asyncio.fixture(scope="function")
async def aio_client_factory(aiohttp_client: AiohttpClient):
    async def _factory(
        response,
    ) -> ClientSession:
        loop = asyncio.get_running_loop()

        app = web.Application(loop=loop)
        app.router.add_get(RELEASE_CHECK_URL, response)

        client: TestClient = await aiohttp_client(app, loop=loop, ssl_shutdown_timeout=0)

        client.session._base_url = URL(
            str(client.server.scheme + "://" + client.server.host + ":" + str(client.server.port))
        )

        return client.session

    return _factory


class TestRunSecurityScan:
    def test_importing_the_hook_does_not_load_presidio(self, modules_loaded_by_importing):
        loaded = modules_loaded_by_importing("src.hooks.run_security_scan")

        assert {"presidio_analyzer", "spacy"}.isdisjoint(loaded)

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

    @pytest.mark.skip("aiohttp upgrade is causing issues with this test")
    async def test_get_version_from_remote_raises_exception_for_http_errors(self, aio_client_factory):
        aio_client = await aio_client_factory(response=lambda _: web.Response(status=404))

        with (
            patch.object(RunSecurityScan, "_get_client_session", return_value=aio_client),
            pytest.raises(ClientResponseError),
        ):
            await RunSecurityScan()._get_version_from_remote()

    async def test_get_version_from_remote_returns_expected_json(self, aio_client_factory):
        aio_client = await aio_client_factory(
            response=lambda _: web.Response(
                status=200, content_type="application/json", text=json.dumps({"tag_name": "v1122"})
            )
        )

        with (
            patch.object(RunSecurityScan, "_get_client_session", return_value=aio_client),
        ):
            assert await RunSecurityScan()._get_version_from_remote() == "v1122"

    async def test_validate_hook_settings_with_bist_hooks_repo_present_without_rev_element_in_pre_commit_file_returns_false(
        self,
    ):
        with (
            patch.object(RunSecurityScan, "_enforce_settings_checks", return_value=True),
        ):
            repo = {"repo": "https://github.com/uktrade/github-standards"}

            assert await RunSecurityScan()._validate_hook_settings(repo) is False

    async def test_validate_hook_settings_with_rev_element_in_pre_commit_file_stores_rev_and_returns_true(self):
        repo = {"repo": "https://github.com/uktrade/github-standards", "rev": "v3"}

        hook = RunSecurityScan()
        assert await hook._validate_hook_settings(repo) is True
        assert hook._version_in_config == "v3"

    async def test_check_remote_version_when_differs_from_remote_version_logs_error(self, caplog):
        with patch.object(RunSecurityScan, "_get_version_from_remote", return_value="v5"):
            logger = LOGGER
            logger.propagate = True  # Enable propagation for this logger

            await RunSecurityScan()._check_remote_version("v3")
            assert caplog.records[-1].levelname == "ERROR"

    async def test_check_remote_version_when_remote_version_http_error_does_not_raise(self):
        mock_get_version_from_remote = AsyncMock()
        mock_get_version_from_remote.side_effect = requests.exceptions.HTTPError
        with patch.object(RunSecurityScan, "_get_version_from_remote", mock_get_version_from_remote):
            await RunSecurityScan()._check_remote_version("v1")

    async def test_check_remote_version_when_matching_remote_version_does_not_raise(self):
        with patch.object(RunSecurityScan, "_get_version_from_remote", return_value="v1"):
            await RunSecurityScan()._check_remote_version("v1")

    async def test_run_security_scan_with_detected_keys_returns_keys(self):
        mock_scan_result = AsyncMock()
        mock_scan_result.return_value.detected_keys = "Keys found"
        with patch("src.hooks.run_security_scan.TrufflehogScanner") as mock_scanner:
            mock_scanner().scan = mock_scan_result
            scan = RunSecurityScan()
            result = await scan.run_security_scan()
            assert result.detected_keys == "Keys found"

    async def test_run_security_scan_without_detected_keys_returns_nothing(self):
        mock_scan_result = AsyncMock()
        mock_scan_result.return_value.detected_keys = None
        with patch("src.hooks.run_security_scan.TrufflehogScanner") as mock_scanner:
            mock_scanner().scan = mock_scan_result
            scan = RunSecurityScan()
            result = await scan.run_security_scan()
            assert result.detected_keys is None

    async def test_run_personal_scan_with_github_action_set_true_calls_scanner_with_all_files_in_git_repo(self):
        with (
            patch("src.hooks.run_security_scan.git.Repo") as mock_repo,
            patch("src.hooks.run_security_scan.PresidioScanner") as mock_scanner,
        ):
            git_file_1 = MagicMock()
            git_file_1.abspath = "1.rt"

            mock_repo.return_value.tree.return_value.traverse.return_value = [git_file_1]

            mock_scanner.return_value = AsyncMock()
            scan = RunSecurityScan(github_action=True, paths=["."])
            await scan.run_personal_scan()
            mock_scanner.assert_called_once_with(False, ["1.rt"])

    async def test_run_personal_scan_with_github_action_set_false_calls_scanner_with_files_in_paths(self):
        with (
            patch("src.hooks.run_security_scan.PresidioScanner") as mock_scanner,
        ):
            mock_scanner.return_value = AsyncMock()
            scan = RunSecurityScan(github_action=False, paths=["1.txt", "2.csv"])
            await scan.run_personal_scan()
            mock_scanner.assert_called_once_with(False, ["1.txt", "2.csv"])

    async def test_run_personal_scan_with_data_detected_returns_expected_results(self):
        detection = PersonalDataDetection(RecognizerResult("test_recognizer", 1, 2, 1), "found value")
        scan_result = PresidioScanResult()
        scan_result.add_path_scan_result(PathScanResult("file.txt", PathScanStatus.FAILED, [detection]))
        mock_scan_result = AsyncMock()
        mock_scan_result.return_value = scan_result
        with patch("src.hooks.run_security_scan.PresidioScanner") as mock_scanner:
            mock_scanner().scan = mock_scan_result
            scan = RunSecurityScan()
            result = await scan.run_personal_scan()

            assert len(result.paths_containing_personal_data) == 1
            assert len(result.paths_without_personal_data) == 0

    async def test_run_personal_scan_without_data_detected_returns_expected_results(self):
        scan_result = PresidioScanResult()
        scan_result.add_path_scan_result(PathScanResult("file.txt", PathScanStatus.PASSED, []))
        mock_scan_result = AsyncMock()
        mock_scan_result.return_value = scan_result
        with patch("src.hooks.run_security_scan.PresidioScanner") as mock_scanner:
            mock_scanner().scan = mock_scan_result
            scan = RunSecurityScan()
            result = await scan.run_personal_scan()

            assert len(result.paths_containing_personal_data) == 0
            assert len(result.paths_without_personal_data) == 1

    @pytest.mark.parametrize(
        "version_in_config,expected_checks",
        [("v1", [call("v1")]), ("", [call("")]), (None, [])],
    )
    async def test_run_starts_remote_version_check_only_when_rev_validated(self, version_in_config, expected_checks):
        with (
            patch.object(RunSecurityScan, "run_security_scan", return_value=TrufflehogScanResult()),
            patch.object(RunSecurityScan, "run_personal_scan", return_value=PresidioScanResult()),
            patch.object(RunSecurityScan, "_check_remote_version") as mock_check_remote_version,
        ):
            hook = RunSecurityScan()
            hook._version_in_config = version_in_config

            await hook.run()

            assert mock_check_remote_version.await_args_list == expected_checks

    async def test_run_with_run_security_scan_true_and_run_personal_scan_true_returns_result_for_both(
        self,
    ):
        with (
            patch.object(RunSecurityScan, "run_security_scan") as mock_run_security_scan,
            patch.object(RunSecurityScan, "run_personal_scan") as mock_run_personal_scan,
        ):
            mock_run_security_scan.return_value = TrufflehogScanResult()
            mock_run_personal_scan.return_value = PresidioScanResult()

            result = await RunSecurityScan().run()
            assert result.trufflehog_scan_result is not None
            assert result.presidio_scan_result is not None

            mock_run_personal_scan.assert_called_once()
            mock_run_security_scan.assert_called_once()

    async def test_run_with_run_security_scan_excluded_does_not_run_a_security_scan(
        self,
    ):
        with (
            patch.object(RunSecurityScan, "run_security_scan") as mock_run_security_scan,
            patch.object(RunSecurityScan, "run_personal_scan") as mock_run_personal_scan,
        ):
            await RunSecurityScan(excluded_scans=[SECURITY_SCAN]).run()

            mock_run_personal_scan.assert_called_once()
            mock_run_security_scan.assert_not_called()

    async def test_run_with_run_personal_data_scan_excluded_does_not_run_a_security_scan(
        self,
    ):
        with (
            patch.object(RunSecurityScan, "run_security_scan") as mock_run_security_scan,
            patch.object(RunSecurityScan, "run_personal_scan") as mock_run_personal_scan,
        ):
            await RunSecurityScan(excluded_scans=[PERSONAL_DATA_SCAN]).run()

            mock_run_personal_scan.assert_not_called()
            mock_run_security_scan.assert_called_once()
