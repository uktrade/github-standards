import sys
import pytest

from aiohttp import web
from src.actions.update_ruleset_version.action import (
    RulesetUpdater,
    main_async,
)
from unittest import mock


class TestAction:
    pytestmark = pytest.mark.asyncio

    async def test_main_async_sends_expected_ruleset_update(self, aio_client_with_app):
        testargs = ["run", "v111", "token abc123", "ruleset_1,ruleset_2"]

        # The check tags function only needs a 200 to verify the tag exists on the repo
        aio_client_with_app.app.router.add_route(
            "GET",
            "/repos/uktrade/github-standards/releases/tags/v111",
            lambda _: web.Response(
                status=200,
            ),
        )

        with (
            open("tests/test_data/get_ruleset.json", mode="r", encoding="utf-8") as read_file,
        ):
            expected_ruleset = read_file.read()
            aio_client_with_app.app.router.add_route(
                "GET",
                "/orgs/uktrade/rulesets/ruleset_1",
                lambda _: web.Response(status=200, text=expected_ruleset, content_type="application/json"),
            )
            aio_client_with_app.app.router.add_route(
                "GET",
                "/orgs/uktrade/rulesets/ruleset_2",
                lambda _: web.Response(status=200, text=expected_ruleset, content_type="application/json"),
            )

        with (
            mock.patch.object(sys, "argv", testargs),
            mock.patch.object(RulesetUpdater, "_get_client_session", return_value=aio_client_with_app),
        ):
            await main_async()

            # TODO - assert the RulesetUpdateRequest._update_ruleset function calls the aio_client_with_app with the correct url and body
