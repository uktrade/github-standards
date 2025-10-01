import argparse
import sys


from typing import List, Optional
from logging import StreamHandler, captureWarnings, INFO, DEBUG, Formatter
from src.hooks.config import LOGGER
from src.hooks.run_security_scan import RunSecurityScan
from src.hooks.trufflehog.vendors import AllowedTrufflehogVendor
from src.hooks.validate_security_scan import ValidateSecurityScan

from src.hooks.hooks_base import Hook


logger = LOGGER


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
    main_parser = argparse.ArgumentParser(description="DBT pre-commit hooks")

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("files", nargs="*", help="Filenames pre-commit has tracked as being changed.", default=[])
    parent_parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", help="output debug logs", default=False
    )

    subparsers = main_parser.add_subparsers(title="subcommands", description="valid subcommands", help="additional help")
    run_scan_parser = subparsers.add_parser("run_scan", parents=[parent_parser])
    run_scan_parser.add_argument(
        "-g",
        "--github-action",
        dest="github_action",
        action="store_true",
        help="Run this hook in a github action",
        required=False,
    )
    run_scan_parser.set_defaults(
        hook=lambda args: RunSecurityScan(
            args.files, args.verbose, args.github_action, allowed_vendor_endpoints=AllowedTrufflehogVendor.all_endpoints()
        )
    )

    validate_scan_parser = subparsers.add_parser("validate_scan", parents=[parent_parser])
    validate_scan_parser.set_defaults(hook=lambda args: ValidateSecurityScan(args.files, args.verbose))

    return main_parser.parse_args(argv)


def main(
    argv: Optional[List[str]] = None,
) -> int:
    if not sys.argv:
        return 1

    args = parse_args(argv)

    init_logger(args.verbose)

    logger.debug("Parsed args: %s", args)

    hook: Hook = args.hook(args)

    logger.debug("Loaded hook class %s", hook)

    is_valid_args = hook.validate_args()
    if not is_valid_args:
        logger.debug("Hook '%s' did not pass args validation check", hook)
        return 1
    logger.debug("Hook '%s' passed args validation check", hook.__class__.__name__)

    is_valid_hook = hook.validate_hook_settings()
    if not is_valid_hook:
        logger.debug("Hook '%s' did not pass hook settings validation check", hook)
        return 1
    logger.debug("Hook '%s' passed hook settings check", hook.__class__.__name__)

    run_result = hook.run()
    if not run_result.success:
        logger.info("Hook '%s' did not successfully run.", hook)
        logger.info("%s", run_result.message)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
