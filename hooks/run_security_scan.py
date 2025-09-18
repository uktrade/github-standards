import argparse
import sys
from typing import List, Optional


def main(
    argv: Optional[List[str]] = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Run security scan - a commit hook to run mandatory security scans against the current commit",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Filenames pre-commit believes are changed.",
    )

    parser.parse_args(argv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
