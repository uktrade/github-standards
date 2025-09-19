import io
import logging

from src.hooks_base import Hook

logger = logging.getLogger()


class ValidateSecurityScan(Hook):
    SIGNED_OFF_BY_TRAILER = "Signed-off-by: DBT pre-commit check"

    def validate_args(self) -> bool:
        if self.files is None or len(self.files) == 0:
            logger.debug("No files passed to hook")
            return False
        if len(self.files) != 1:
            logger.debug(
                "Only a single filename can be provided to this hook, there were %s files provided", len(self.files)
            )
            return False
        logger.debug("Hook '%s' validation passed", self.__class__.__name__)
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

            new_commit_message = f"{commit_msg}\n\n{self.SIGNED_OFF_BY_TRAILER}"
            logger.debug("New commit message is %s", new_commit_message)

            fd.seek(0)
            fd.writelines(new_commit_message)
            fd.truncate()
            logger.info("Commit message updated")

            return True
