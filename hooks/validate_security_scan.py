import argparse
import io
import sys

from typing import List, Optional
from logging import StreamHandler, captureWarnings, getLogger, INFO, DEBUG

LOG = getLogger()
SIGNED_OFF_BY_TRAILER = "Signed-off-by: DBT pre-commit check"


def _init_logger(args):
    """Initialize the logger.

    :param debug: Whether to enable debug mode
    :return: An instantiated logging instance
    """
    log_level = DEBUG if args.verbose else INFO
    LOG.handlers = []

    captureWarnings(True)

    LOG.setLevel(log_level)
    handler = StreamHandler(sys.stderr)
    LOG.addHandler(handler)
    LOG.debug("Logging initialized with level %s", log_level)


def update_git_message(filename):
    LOG.debug("Reading contents from %s", filename)
    with io.open(filename, "r+") as fd:
        contents = fd.readlines()
        LOG.debug("Commit message for %s is %s", filename, contents)
        if not contents:
            LOG.info("No commit message provided")
            return 1

        commit_msg = contents[0].rstrip("\r\n")

        new_commit_message = f"{commit_msg}\n\n{SIGNED_OFF_BY_TRAILER}"
        LOG.debug("New commit message is %s", new_commit_message)

        fd.seek(0)
        fd.writelines(new_commit_message)
        fd.truncate()
        LOG.info("Commit message updated")
        return 0


def validate_args(args):
    if args.filename is None or len(args.filename) == 0:
        LOG.debug("No filename passed to hook")
        return False
    return True


def main(
    argv: Optional[List[str]] = None,
) -> int:  # when alled from pre-commit argv will always be None
    parser = argparse.ArgumentParser(
        description="Validate security scan - a commit hook to verify mandatory security scans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("filename")

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="output extra information like excluded and included files",
    )

    parser.set_defaults(verbose=False)

    args = parser.parse_args(argv)

    _init_logger(args)

    if not validate_args(args):
        return 1

    return update_git_message(args.filename)


if __name__ == "__main__":
    sys.exit(main())
