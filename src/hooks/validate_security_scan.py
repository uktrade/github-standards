import io
import logging

from src.config import MANDATORY_HOOK_IDS, PRE_COMMIT_FILE, SIGNED_OFF_BY_TRAILER
from src.hooks_base import Hook

logger = logging.getLogger()


class ValidateSecurityScan(Hook):
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

    def _validate_hook_settings(self, dbt_repo_config) -> bool:
        if "hooks" not in dbt_repo_config:
            logger.info("File %s contains the dbt hooks repo, but is missing the hooks child element", PRE_COMMIT_FILE)
            return False

        dbt_hook_ids = [hook["id"] for hook in dbt_repo_config["hooks"] if "id" in hook]
        if not dbt_hook_ids:
            logger.info("File %s contains the dbt hooks repo, but is missing the hooks to run", PRE_COMMIT_FILE)
            return False

        for mandatory_hook in MANDATORY_HOOK_IDS:
            if mandatory_hook not in dbt_hook_ids:
                logger.info("File %s does not contain the mandatory hook '%s'", PRE_COMMIT_FILE, mandatory_hook)
                return False

        return True

    def run(self) -> bool:
        commit_msg_file = self.files[0]
        logger.debug("Reading contents from %s", commit_msg_file)
        with io.open(commit_msg_file, "r+") as fd:
            contents = fd.readlines()
            logger.debug("Commit message for %s is %s", commit_msg_file, contents)
            if not contents:
                logger.info("No commit message provided")
                return False

            commit_msg = contents[0].rstrip("\r\n")

            new_commit_message = f"{commit_msg}\n\n{SIGNED_OFF_BY_TRAILER}"
            logger.debug("New commit message is %s", new_commit_message)

            fd.seek(0)
            fd.writelines(new_commit_message)
            fd.truncate()
            logger.info("Commit message updated")

            return True
