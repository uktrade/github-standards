import re

from pathlib import Path

from anyio import run_process

from src.hooks.config import LOGGER, MANDATORY_HOOK_IDS, PRE_COMMIT_FILE, SIGNED_OFF_BY_TRAILER
from src.hooks.hooks_base import Hook, HookRunResult

logger = LOGGER

# The line `git commit -v` puts above the diff, starting with the comment character
SCISSORS_LINE = re.compile(rb"^(\S+) -{24} >8 -{24}$", flags=re.MULTILINE)


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

    async def _validate_hook_settings(self, bist_repo_config) -> bool:
        if "hooks" not in bist_repo_config:
            logger.info(
                "File %s contains the github standards hooks repo, but is missing the hooks child element", PRE_COMMIT_FILE
            )
            return False

        bist_hook_ids = [hook["id"] for hook in bist_repo_config["hooks"] if "id" in hook]
        if not bist_hook_ids:
            logger.info("File %s contains the github standards hooks repo, but is missing the hooks to run", PRE_COMMIT_FILE)
            return False

        for mandatory_hook in MANDATORY_HOOK_IDS:
            if mandatory_hook not in bist_hook_ids:
                logger.info("File %s does not contain the mandatory hook '%s'", PRE_COMMIT_FILE, mandatory_hook)
                return False

        return True

    async def run(self) -> ValidateSecurityScanResult:
        commit_msg_file = self.paths[0]  # type: ignore
        commit_msg_path = Path(commit_msg_file)
        logger.debug("Reading contents from %s", commit_msg_file)
        # git edits the file whatever its encoding so decode the message only for logging
        message = commit_msg_path.read_bytes()

        logger.debug("Commit message for %s is %s", commit_msg_file, message.decode(errors="replace"))
        if not message:
            logger.debug("No commit message provided")
            return ValidateSecurityScanResult(False, "No commit message provided")

        if not message.endswith(b"\n"):
            # Without a final newline, older git (such as the image's 2.39) adds the trailer to the last paragraph,
            # where git doesn't recognise it as a trailer
            with commit_msg_path.open("ab") as fd:
                fd.write(b"\n")

        # Inside the hook's container git can't see the user's global config so take a custom comment character from
        # the scissors line. Otherwise the trailer lands below that line and git discards it with the diff
        git_config = []
        scissors_line = SCISSORS_LINE.search(message)
        if scissors_line:
            git_config = ["-c", f"core.commentChar={scissors_line.group(1).decode(errors='replace')}"]

        # addIfDifferent stops git adding the trailer again when another Signed-off-by line follows it. Both options
        # also override trailer.* settings in the repo's git config
        git_result = await run_process(
            [
                "git",
                *git_config,
                "interpret-trailers",
                "--in-place",
                "--if-exists",
                "addIfDifferent",
                "--if-missing",
                "add",
                "--trailer",
                SIGNED_OFF_BY_TRAILER,
                commit_msg_file,
            ],
            check=False,
        )
        if git_result.returncode != 0:
            error = git_result.stderr.decode(errors="replace").strip()
            return ValidateSecurityScanResult(False, f"Unable to add the {SIGNED_OFF_BY_TRAILER} trailer: {error}")

        logger.debug("New commit message is %s", commit_msg_path.read_bytes().decode(errors="replace"))
        logger.info("Commit message updated")

        return ValidateSecurityScanResult(True)
