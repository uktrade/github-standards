import argparse
import sys


from typing import List, Optional
from logging import StreamHandler, captureWarnings, getLogger, INFO, DEBUG, Formatter
from src.hooks.run_security_scan import RunSecurityScan
from src.hooks.validate_security_scan import ValidateSecurityScan

from src.hooks.hooks_base import Hook

logger = getLogger()

hooks: dict[str, Hook] = {
    "run-security-scan": RunSecurityScan,
    "validate-security-scan": ValidateSecurityScan,
}


def get_hook_class(hook_id) -> Hook | None:
    if hook_id not in hooks:
        return None
    return hooks[hook_id]


def init_logger(verbose):
    log_level = DEBUG if verbose else INFO
    logger.handlers = []

    captureWarnings(True)

    logger.setLevel(log_level)
    handler = StreamHandler(sys.stderr)
    formatter = Formatter(fmt="%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.debug("Logging initialized with level %s", log_level)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run security scan - a commit hook to run mandatory security scans against the current commit",
    )
    parser.add_argument("--hook-id", help="The id of the hook to run", required=True)
    parser.add_argument("files", nargs="*", help="Filenames pre-commit believes are changed.", default=[])

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="output debug logs", default=False)

    return parser.parse_args(argv)


def main(
    argv: Optional[List[str]] = None,
) -> int:
    if not sys.argv:
        return 1

    args = parse_args(argv)

    init_logger(args.verbose)

    logger.debug("Parsed args: %s", args)

    hook_class = get_hook_class(args.hook_id)
    if not hook_class:
        logger.debug("Hook id '%s' is not a known hook", args.hook_id)
        return 1

    hook: Hook = hook_class(args.files, args.verbose)

    logger.debug("Loaded hook class %s using id '%s'", hook, args.hook_id)

    is_valid_args = hook.validate_args()
    if not is_valid_args:
        logger.debug("Hook '%s' did not pass args validation check", args.hook_id)
        return 1
    logger.debug("Hook '%s' passed args validation check", hook.__class__.__name__)

    is_valid_hook = hook.validate_hook_settings()
    if not is_valid_hook:
        logger.debug("Hook '%s' did not pass hook settings validation check", args.hook_id)
        return 1
    logger.debug("Hook '%s' passed hook settings check", hook.__class__.__name__)

    run_result = hook.run()
    if not run_result.success:
        logger.info("Hook '%s' did not successfully run.", args.hook_id)
        logger.info("%s", run_result.message)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
