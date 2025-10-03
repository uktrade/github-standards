import logging
import requests

from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.settings import default_settings

from src.config import PRE_COMMIT_FILE, RELEASE_CHECK_URL
from src.hooks_base import Hook, HookRunResult

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
        DATADOG_APP_KEY = "0100000000000000000000000000000000000000"
        DD_APP_KEY = "0100000000000000000000000000000000000000"

        logger.info("Testing fake app key %s", DATADOG_APP_KEY)
        logger.info("Testing fake app key %s", DD_APP_KEY)
        with default_settings():
            secrets = SecretsCollection()
            secrets.scan_files(*self.files)

            if secrets.data:
                logger.debug("This security scan failed due to secrets being detected")
                return HookRunResult(False, secrets.json())

            return HookRunResult(True)
