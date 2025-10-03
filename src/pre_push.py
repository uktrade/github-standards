import argparse
from logging import DEBUG, StreamHandler, getLogger, captureWarnings
import sys
from typing import List, Optional

logger = getLogger()


def main(
    argv: Optional[List[str]] = None,
) -> int:
    log_level = DEBUG
    logger.handlers = []

    captureWarnings(True)

    logger.setLevel(log_level)
    handler = StreamHandler(sys.stderr)
    logger.addHandler(handler)

    logger.debug("sys.args %s", sys.argv)
    if not sys.argv:
        return 1

    parser = argparse.ArgumentParser(
        description="Run security scan - a commit hook to run mandatory security scans against the current commit",
    )
    parser.add_argument("--hook-id", help="The id of the hook to run", required=True)
    parser.add_argument("files", nargs="*", help="Filenames pre-commit believes are changed.", default=[])

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="output debug logs", default=False)

    parsed = parser.parse_args(argv)
    logger.debug("parsed %s", parsed)


if __name__ == "__main__":
    sys.exit(main())
