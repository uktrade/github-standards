import os
import aiohttp
import anyio
import argparse
import asyncio
import logging
import sys

from logging import StreamHandler, captureWarnings, DEBUG, Formatter
from typing import List, Optional


ORG_WORKFLOW_REPOSITORY_ID = os.environ.get("ORG_WORKFLOW_REPOSITORY_ID")
LOGGER = logging.getLogger("update-ruleset-version")


class TagDoesNotExistException(Exception):
    def __init__(self, tag: str, *args: object) -> None:
        super().__init__(f"The git tag {tag} does not exist")


class RulesetUpdateRequest:
    def __init__(self, tag: str, ruleset_id: int) -> None:
        self.tag = tag
        self.ruleset_id = ruleset_id

    async def use_latest_tag(self, session):
        ruleset = await self._get_ruleset(self.ruleset_id, session)
        self._update_ruleset_workflow_tag(ruleset)
        await self._update_ruleset(self.ruleset_id, ruleset, session)

    async def _update_ruleset(self, ruleset_id, ruleset, session):
        # Until a way is found to re-trigger the PR checks, pause here for now
        pass

    def _update_ruleset_workflow_tag(self, ruleset):
        ruleset.pop("id", None)
        # make sure to remove id from the json, as sending this in the payload body will cause an error
        # only update rules that match the repository_id
        rules = ruleset["rules"]
        for rule in rules:
            if rule["type"] == "workflows":
                for workflow in rule["parameters"]["workflows"]:
                    if str(workflow["repository_id"]) == str(ORG_WORKFLOW_REPOSITORY_ID):
                        current_workflow_ref = workflow["ref"]
                        new_workflow_ref = f"refs/tags/{self.tag}"
                        workflow["ref"] = new_workflow_ref
                        LOGGER.debug("Updated workflow from %s to %s", current_workflow_ref, new_workflow_ref)
        return ruleset

    async def _get_ruleset(self, ruleset_id: int, session: aiohttp.ClientSession):
        LOGGER.debug("Calling get ruleset for id %s", ruleset_id)
        async with session.get(
            f"/orgs/uktrade/rulesets/{ruleset_id}",
            raise_for_status=True,
        ) as response:
            LOGGER.debug("Received %s response for get ruleset for id %s", response.status, ruleset_id)
            return await response.json()


class RulesetUpdater:
    def __init__(self, tag: str, token: str) -> None:
        self.tag = tag
        self.token = token

    async def _check_tag_exists(self, session: aiohttp.ClientSession) -> bool:
        LOGGER.debug("Checking the tag %s exists", self.tag)

        async with session.get(
            f"/repos/uktrade/github-standards/releases/tags/{self.tag}",
        ) as response:
            LOGGER.debug("Response from %s was %s", response.real_url, response.status)
            if response.status == 404:
                return False
            response.raise_for_status()
            return True

    def _get_client_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            base_url="https://api.github.com",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f"Bearer {self.token}",
            },
        )

    async def update(self, ruleset_ids: List[int]):
        session = self._get_client_session()
        tag_exists = await self._check_tag_exists(session)
        if tag_exists:
            ruleset_tasks = {}

            async with asyncio.TaskGroup() as tg:
                for ruleset_id in ruleset_ids:
                    request = RulesetUpdateRequest(self.tag, ruleset_id)
                    ruleset_tasks[ruleset_id] = tg.create_task(request.use_latest_tag(session))

            await session.close()

        else:
            raise TagDoesNotExistException(self.tag)


def init_logger():
    log_level = DEBUG
    LOGGER.handlers = []

    captureWarnings(True)

    LOGGER.setLevel(log_level)
    handler = StreamHandler(sys.stderr)
    formatter = Formatter(fmt="%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.propagate = False

    LOGGER.debug("Logging initialized with level %s", log_level)


def parse_args(argv):
    class SplitArgs(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values.split(","))

    parser = argparse.ArgumentParser(description="Update the org ruleset versions")
    parser.add_argument("tag", help="The new tag to use")
    parser.add_argument("token", help="The github token")
    parser.add_argument("ruleset_ids", help="The ids of the ruleset to update in a comma separate string", action=SplitArgs)

    return parser.parse_args(argv)


async def main_async(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    init_logger()
    LOGGER.debug(
        "Updating rulesets %s to tag %s using repository %s", args.ruleset_ids, args.tag, ORG_WORKFLOW_REPOSITORY_ID
    )
    ruleset_updater = RulesetUpdater(args.tag, args.token)
    await ruleset_updater.update(args.ruleset_ids)


def main(argv: Optional[List[str]] = None):
    if not sys.argv:
        return 1
    return anyio.run(main_async, argv)


if __name__ == "__main__":
    sys.exit(main())
