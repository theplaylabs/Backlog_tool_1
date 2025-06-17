"""Command-line interface for the Backlog CLI tool.

Reads a single line of dictation from **stdin**, sends it to the OpenAI client, and
prepends the structured entry to `backlog.csv` in the current directory.  A
`--dry-run` flag lets you preview the JSON without touching the CSV (handy for
unit tests).

Exit codes: 0 success, 1 user error, 2 API/network error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__ as _VERSION
from . import csv_store, openai_client, config


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bckl",
        description="Dictation-driven backlog entry tool",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print JSON output but do not write to CSV",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging (currently prints JSON).",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"bckl {_VERSION}",
    )
    return p


def main(argv: list[str] | None = None) -> None:  # noqa: D401
    """Program entry point."""
    argv = argv if argv is not None else sys.argv[1:]
    parser = _build_parser()

    # Ensure logging configured early
    logger = config.get_logger(__name__)
    args = parser.parse_args(argv)

    # Read single line dictation from stdin
    try:
        dictation = sys.stdin.readline()
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(1)

    if not dictation.strip():
        parser.error("No input received – please dictate or type a line and press Enter.")

    try:
        data = openai_client.call_openai(dictation)
    except Exception as exc:  # broad: translate to exit code 2
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        print(json.dumps(data, indent=2))
        logger.info("Dry-run output for dictation: %s", dictation.strip())
        sys.exit(0)

    # Attempt to write to CSV
    csv_path = Path.cwd() / "backlog.csv"
    
    # Create empty file if it doesn't exist
    if not csv_path.exists():
        logger.info("Creating new backlog.csv file")
        try:
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                pass  # Just create an empty file
        except Exception as exc:
            print(f"ERROR creating CSV file: {exc}", file=sys.stderr)
            sys.exit(2)
    
    try:
        csv_store.prepend_row(
            csv_path,
            [data["title"], str(data["difficulty"]), data["description"], data["timestamp"]],
        )
    except NotImplementedError:
        # Development placeholder
        print("(CSV persistence not yet implemented – dry run implied)")
    except Exception as exc:  # pragma: no cover
        print(f"ERROR saving CSV: {exc}", file=sys.stderr)
        sys.exit(2)

    # Print separator line before output
    separator = "-" * 24
    print(separator)
    print(f"{data['title']} ({data['difficulty']}) saved")
    print(separator)
    
    # Always print the full description
    print(data["description"])
    
    logger.info("Entry saved: %s", data['title'])

    sys.exit(0)

if __name__ == "__main__":
    main()
