import json
import pytest
import sys

from aiohttp import ClientResponseError, web

from src.actions.update_ruleset_version import action
from src.actions.update_ruleset_version.action import (
    RulesetUpdateRequest,
    RulesetUpdater,
    TagDoesNotExistException,
    main_async,
    main as main_function,
    parse_args,
)
from unittest import mock
from unittest.mock import AsyncMock, call, patch


class TestAction:
    class TestParseArgs:
        def test_parse_args_without_args_returns_error(self):
            testargs = [""]
            with mock.patch.object(sys, "argv", testargs), pytest.raises(SystemExit):
                parse_args(testargs)

        def test_parse_args_with_single_ruleset_returns_expected_args(
            self,
        ):
            testargs = ["v111", "token abc123", "r1"]
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.tag == "v111"
                assert result.token == "token abc123"
                assert result.ruleset_ids == ["r1"]

        def test_parse_args_with_multiple_rulesets_returns_expected_args(
            self,
        ):
            testargs = ["v111", "token abc123", "r1,r2,r3"]
            with mock.patch.object(sys, "argv", testargs):
                result = parse_args(testargs)
                assert result.tag == "v111"
                assert result.token == "token abc123"
                assert result.ruleset_ids == ["r1", "r2", "r3"]

    class TestMain:
        async def test_no_arguments_provided_returns_expected_error(self):
            testargs = []
            with mock.patch.object(sys, "argv", testargs):
                assert main_function(testargs) == 1

    class TestMainAsync:
        async def test_main_async_calls_update_with_expected_args(self):
            testargs = ["run", "v111", "token abc123", "r1,r2"]
            init_mock = mock.MagicMock()
            init_mock.return_value = None
            update_mock = mock.AsyncMock()

            with (
                mock.patch.object(sys, "argv", testargs),
                mock.patch.multiple(RulesetUpdater, __init__=init_mock, update=update_mock),
            ):
                await main_async()

                init_mock.assert_called_once_with("v111", "token abc123")
                update_mock.assert_awaited_once_with(["r1", "r2"])


class TestRulesetUpdater:
    pytestmark = pytest.mark.asyncio

    async def test_check_tag_exists_returns_false_when_tag_does_not_exist(self, aio_client_with_app):
        updater = RulesetUpdater("tag1", "token1")

        aio_client_with_app.app.router.add_route(
            "GET",
            f"/repos/uktrade/github-standards/releases/tags/{updater.tag}",
            lambda _: web.Response(status=404),
        )
        assert await updater._check_tag_exists(aio_client_with_app) is False

    async def test_check_tag_exists_raises_exception_when_token_is_invalid(self, aio_client_with_app):
        updater = RulesetUpdater("tag1", "token1")

        aio_client_with_app.app.router.add_route(
            "GET",
            f"/repos/uktrade/github-standards/releases/tags/{updater.tag}",
            lambda _: web.Response(status=401),
        )
        with pytest.raises(ClientResponseError):
            assert await updater._check_tag_exists(aio_client_with_app) is False

    async def test_check_tag_exists_returns_true_when_tag_exists(self, aio_client_with_app):
        updater = RulesetUpdater("tag1", "token1")

        aio_client_with_app.app.router.add_route(
            "GET",
            f"/repos/uktrade/github-standards/releases/tags/{updater.tag}",
            lambda _: web.Response(status=200),
        )
        assert await updater._check_tag_exists(aio_client_with_app) is True

    async def test_update_raises_exception_when_tag_does_not_exits(self, aio_client_with_app):
        updater = RulesetUpdater("tag1", "token1")

        with (
            patch.object(RulesetUpdater, "_check_tag_exists", return_value=False),
            patch.object(RulesetUpdater, "_get_client_session", return_value=aio_client_with_app),
            pytest.raises(TagDoesNotExistException),
        ):
            await updater.update([1, 2])

    async def test_update_runs_update_for_each_ruleset(self, aio_client_with_app):
        updater = RulesetUpdater("tag1", "token1")

        with (
            patch.object(RulesetUpdater, "_check_tag_exists", return_value=True),
            patch.object(RulesetUpdater, "_get_client_session", return_value=aio_client_with_app),
            patch("src.actions.update_ruleset_version.action.RulesetUpdateRequest") as mock_ruleset_update_request,
        ):
            mock_ruleset_update_request.return_value.use_latest_tag = AsyncMock()
            await updater.update([1, 2])
            mock_ruleset_update_request.return_value.use_latest_tag.assert_has_calls(
                [call(aio_client_with_app), call(aio_client_with_app)]
            )


class TestRulesetUpdateRequest:
    pytestmark = pytest.mark.asyncio

    async def test_use_latest_tag(self, aio_client_with_app):
        mock_ruleset_response = {
            "id": 1,
            "rules": [{"type": "workflows", "parameters": {"workflows": []}}],
        }

        mock_get_ruleset = AsyncMock(return_value=mock_ruleset_response)
        mock_update_ruleset_workflow_tag = mock.MagicMock()
        mock_update_ruleset = AsyncMock()

        with patch.multiple(
            RulesetUpdateRequest,
            _get_ruleset=mock_get_ruleset,
            _update_ruleset_workflow_tag=mock_update_ruleset_workflow_tag,
            _update_ruleset=mock_update_ruleset,
        ):
            ruleset_request = RulesetUpdateRequest("v1", 5)

            await ruleset_request.use_latest_tag(aio_client_with_app)
            mock_get_ruleset.assert_called_once_with(5, aio_client_with_app)
            mock_update_ruleset.assert_called_once_with(5, mock_ruleset_response, aio_client_with_app)

    def test_update_ruleset_workflow_tag_removes_id_from_json(self):
        with open("tests/test_data/get_ruleset.json", mode="r", encoding="utf-8") as read_file:
            test_ruleset = json.load(read_file)

            ruleset_request = RulesetUpdateRequest("v1", 2)
            updated = ruleset_request._update_ruleset_workflow_tag(test_ruleset)
            assert "id" not in updated

    def test_update_ruleset_workflow_tag_does_not_change_workflow_refs_for_workflows_not_using_repository(self):
        with (
            open("tests/test_data/get_ruleset.json", mode="r", encoding="utf-8") as read_file,
            patch.object(action, "ORG_WORKFLOW_REPOSITORY_ID", 1234),
        ):
            test_ruleset = json.load(read_file)

            ruleset_request = RulesetUpdateRequest("new_tag", 2)
            workflows = ruleset_request._update_ruleset_workflow_tag(test_ruleset)["rules"][1]["parameters"]["workflows"]

            assert workflows[2]["ref"] == "refs/main"

    def test_update_ruleset_workflow_tag_updates_workflow_refs_for_workflows_using_repository(self):
        with (
            open("tests/test_data/get_ruleset.json", mode="r", encoding="utf-8") as read_file,
            patch.object(action, "ORG_WORKFLOW_REPOSITORY_ID", 1234),
        ):
            test_ruleset = json.load(read_file)
            new_tag = "v34.7.1"

            ruleset_request = RulesetUpdateRequest(new_tag, 2)
            workflows = ruleset_request._update_ruleset_workflow_tag(test_ruleset)["rules"][1]["parameters"]["workflows"]

            assert workflows[0]["ref"] == f"refs/tags/{new_tag}"
            assert workflows[1]["ref"] == f"refs/tags/{new_tag}"

    async def test_get_ruleset_throws_exception_when_http_call_fails(self, aio_client_with_app):
        ruleset_request = RulesetUpdateRequest("v1", 2)
        aio_client_with_app.app.router.add_route(
            "GET",
            f"/orgs/uktrade/rulesets/{ruleset_request.ruleset_id}",
            lambda _: web.Response(status=401),
        )
        with pytest.raises(ClientResponseError):
            await ruleset_request._get_ruleset(ruleset_request.ruleset_id, aio_client_with_app)

    async def test_get_ruleset_returns_expected_json(self, aio_client_with_app):
        ruleset_request = RulesetUpdateRequest("v1", 5)
        with (
            open("tests/test_data/get_ruleset.json", mode="r", encoding="utf-8") as read_file,
        ):
            expected_ruleset = read_file.read()
            aio_client_with_app.app.router.add_route(
                "GET",
                f"/orgs/uktrade/rulesets/{ruleset_request.ruleset_id}",
                lambda _: web.Response(status=200, text=expected_ruleset, content_type="application/json"),
            )
            ruleset = await ruleset_request._get_ruleset(ruleset_request.ruleset_id, aio_client_with_app)
            assert ruleset == json.loads(expected_ruleset)
