import io
import logging
import yaml

from pathlib import Path
from src.hooks_base import Hook

logger = logging.getLogger()


class ValidateSecurityScan(Hook):
    # TODO can these all get moved to configs and out of code
    SIGNED_OFF_BY_TRAILER = "Signed-off-by: DBT pre-commit check"
    PRE_COMMIT_FILE = ".pre-commit-config.yaml"
    MANDATORY_HOOK_IDS = ["validate-security-scan", "run-security-scan"]

    def validate_args(self) -> bool:
        if self.files is None or len(self.files) == 0:
            logger.debug("No files passed to hook")
            return False
        if len(self.files) != 1:
            logger.debug(
                "Only a single filename can be provided to this hook, there were %s files provided", len(self.files)
            )
            return False

        return True

    def _skip_check(self) -> bool:
        """If this check is ran in the dbt-hooks repository, it will always fail as we use a local hook implementation for running the pre-commit hooks. This ensures we are always running the latest local version, and will catch any development errors early before creating a tagged docker image as part of releasing.

        Returns:
            bool: Whether this check should be skipped
        """
        return "site-packages" not in __file__

    def validate_hooks(self) -> bool:
        if self._skip_check():
            logger.debug("This hook is being run inside the dbt-hooks repo, it can be ignored")
            return True

        if not Path(self.PRE_COMMIT_FILE).exists():
            logger.info("File %s does not exist in this repository. This file must be present", self.PRE_COMMIT_FILE)
            return False

        with open(self.PRE_COMMIT_FILE, "r") as file:
            config = yaml.safe_load(file)
            if "repos" not in config:
                logger.info("File %s does not contain a repo tag", self.PRE_COMMIT_FILE)
                return False

            dbt_hook_repo = list(filter(lambda x: "https://github.com/uktrade/dbt-hooks" in x["repo"], config["repos"]))
            if not dbt_hook_repo:
                logger.info("File %s does not contain the dbt hooks repo", self.PRE_COMMIT_FILE)
                return False
            if len(dbt_hook_repo) != 1:
                logger.info("File %s can only contain one dbt-hooks repo entry", self.PRE_COMMIT_FILE)
                return False

            if "hooks" not in dbt_hook_repo[0]:
                logger.info(
                    "File %s contains the dbt hooks repo, but is missing the hooks child element", self.PRE_COMMIT_FILE
                )
                return False

            dbt_hook_ids = [hook["id"] for hook in dbt_hook_repo[0]["hooks"] if "id" in hook]
            if not dbt_hook_ids:
                logger.info("File %s contains the dbt hooks repo, but is missing the hooks to run", self.PRE_COMMIT_FILE)
                return False

            for mandatory_hook in self.MANDATORY_HOOK_IDS:
                if mandatory_hook not in dbt_hook_ids:
                    logger.info("File %s does not contain the mandatory hook '%s'", self.PRE_COMMIT_FILE, mandatory_hook)
                    return False

            return True

    def run(self) -> bool:
        is_valid = self.validate_hooks()
        if not is_valid:
            logger.info("Validation failed when checking security hooks were run")
            return False

        commit_msg_file = self.files[0]
        logger.debug("Reading contents from %s", commit_msg_file)
        with io.open(commit_msg_file, "r+") as fd:
            contents = fd.readlines()
            logger.debug("Commit message for %s is %s", commit_msg_file, contents)
            if not contents:
                logger.info("No commit message provided")
                return False

            commit_msg = contents[0].rstrip("\r\n")

            new_commit_message = f"{commit_msg}\n\n{self.SIGNED_OFF_BY_TRAILER}"
            logger.debug("New commit message is %s", new_commit_message)

            fd.seek(0)
            fd.writelines(new_commit_message)
            fd.truncate()
            logger.info("Commit message updated")

            return True
