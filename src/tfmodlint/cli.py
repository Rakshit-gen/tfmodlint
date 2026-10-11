"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tfmodlint import __version__, report
from tfmodlint.module import ParseError, load_module
from tfmodlint.rules import ERROR, lint

EXIT_OK, EXIT_PROBLEMS, EXIT_ERROR = 0, 1, 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tfmodlint", description="Lint Terraform modules for problems that hurt reuse."
    )
    parser.add_argument("paths", nargs="*", default=["."], help="module directories (default: .)")
    parser.add_argument(
        "--strict", action="store_true", help="exit 1 on warnings too, not only on errors"
    )
    parser.add_argument("--version", action="version", version=f"tfmodlint {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = []
    try:
        for raw in args.paths:
            path = Path(raw)
            if not path.is_dir():
                raise ParseError(f"{raw}: not a directory")
            module = load_module(path)
            if not module.sources:
                raise ParseError(f"{raw}: no .tf files")
            findings += lint(module)
    except (OSError, ParseError) as exc:
        print(f"tfmodlint: {exc}", file=sys.stderr)
        return EXIT_ERROR

    sys.stdout.write(report.text(findings))
    if any(f.level == ERROR or args.strict for f in findings):
        return EXIT_PROBLEMS
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
