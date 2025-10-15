import logging
import requests


from src.hooks.config import PRE_COMMIT_FILE, RELEASE_CHECK_URL
from src.hooks.hooks_base import Hook, HookRunResult

logger = logging.getLogger()


class RunSecurityScan(Hook):
    def validate_args(self) -> bool:
        # pre-commit can have files, but can also be passed nothing
        return True

    def _get_version_from_remote(self):
        req = requests.get(
            RELEASE_CHECK_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=3,  # This is a low timeout, we don't want to block commits or make devs wait for the github api
        )
        req.raise_for_status()
        content = req.json()
        return content["tag_name"]

    def _validate_hook_settings(self, dbt_repo_config):
        if "rev" not in dbt_repo_config:
            logger.debug("File %s contains the dbt hooks repo, but is missing the rev child element", PRE_COMMIT_FILE)
            return False

        # If the call to get the remote version fails, return True as we don't want this to block a dev from commiting in this scenario.
        try:
            version_in_config = dbt_repo_config["rev"]
            version_in_remote = self._get_version_from_remote()

            if version_in_config != version_in_remote:
                logger.info(
                    "The version in your local config is %s, but the latest version is %s. Run `pre-commit autoupdate` to update to the latest version",
                    version_in_config,
                    version_in_remote,
                )
                return False
        except Exception:
            logger.exception("The remote version check failed", stack_info=True)
            return True

        return True

    def run(self) -> HookRunResult:
        return HookRunResult(True)
