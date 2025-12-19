import io
import re

from src.hooks.config import LOGGER, MANDATORY_HOOK_IDS, PRE_COMMIT_FILE, SIGNED_OFF_BY_TRAILER
from src.hooks.hooks_base import Hook, HookRunResult

logger = LOGGER


class ValidateSecurityScanResult(HookRunResult):
    def __init__(self, success: bool, message: str | None = None):
        self.success = success
        self.message = message

    def run_success(self) -> bool:
        return self.success

    def run_summary(self) -> str | None:
        return self.message


class ValidateSecurityScan(Hook):
    def validate_args(self) -> bool:
        if self.paths is None or len(self.paths) == 0:
            logger.debug("No files passed to hook, this hook needs 1 file")
            return False
        if len(self.paths) != 1:
            logger.debug(
                "Only a single filename can be provided to this hook, there were %s files provided", len(self.paths)
            )
            return False

        return True

    async def _validate_hook_settings(self, dbt_repo_config) -> bool:
        if "hooks" not in dbt_repo_config:
            logger.info(
                "File %s contains the github standards hooks repo, but is missing the hooks child element", PRE_COMMIT_FILE
            )
            return False

        dbt_hook_ids = [hook["id"] for hook in dbt_repo_config["hooks"] if "id" in hook]
        if not dbt_hook_ids:
            logger.info("File %s contains the github standards hooks repo, but is missing the hooks to run", PRE_COMMIT_FILE)
            return False

        for mandatory_hook in MANDATORY_HOOK_IDS:
            if mandatory_hook not in dbt_hook_ids:
                logger.info("File %s does not contain the mandatory hook '%s'", PRE_COMMIT_FILE, mandatory_hook)
                return False

        return True

    async def run(self) -> ValidateSecurityScanResult:
        commit_msg_file = self.paths[0]  # type: ignore
        logger.debug("Reading contents from %s", commit_msg_file)
        with io.open(commit_msg_file, "r+", encoding="utf-8") as fd:
            contents = fd.readlines()

            logger.debug("Commit message for %s is %s", commit_msg_file, "".join(contents))
            if not contents:
                logger.debug("No commit message provided")
                return ValidateSecurityScanResult(False, "No commit message provided")

            regex = re.compile(r"Signed-off-by", flags=re.DOTALL)
            filtered_contents = [i for i in contents if not regex.match(i)]
            filtered_contents.append(f"\n{SIGNED_OFF_BY_TRAILER}")
            logger.debug("New commit message is %s", "".join(filtered_contents))

            fd.seek(0)
            fd.writelines(filtered_contents)
            fd.truncate()
            logger.info("Commit message updated")

            return ValidateSecurityScanResult(True)
